import sys, os
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
print("Loading models...", flush=True)
p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

candidate_sets = {
    "headings": [
        "Hardware Security and Memory Safety.",
        "Handling Deletions with Bloom Filters.",
        "Background Workers and Memory Cleanup.",
        "Encryption Speed and Memory Lifetime.",
        "Search Speed Across Test Devices.",
        "Updating Files and Filter Scaling.",
        "Network Delays and Traffic Smoothing.",
        "Storage Overhead and Battery Draw.",
        "Cold Cache Lookups and Multi-Query Tests."
    ],
    "related_intro": [
        "Early searchable encryption started in 2000.",
        "Curtmola formalized security games for encrypted search in 2006.",
        "Later schemes supported dynamic file additions.",
        "Patel used fixed bins to reduce match leakage.",
        "Table I compares our scheme with existing systems.",
        "When handling large collections, users can choose wider buckets to save data."
    ],
    "fig_captions_short": [
        "System architecture across mobile client, network channel, and cloud storage.",
        "Volume padding comparison between unpadded queries and VisioCrypt power-of-two buckets.",
        "File encryption throughput and RAM secret key persistence across test phones.",
        "Search query latency across tested smartphone tiers."
    ]
}

all_sents = []
mapping = []
for key, sents in candidate_sets.items():
    for s in sents:
        all_sents.append(s)
        mapping.append(key)

print(f"Scoring {len(all_sents)} sentences across {len(candidate_sets)} sets...", flush=True)
pa = p_ahmed(all_sents, batch_size=32)
pf = p_fakespot(all_sents, batch_size=32)
po = p_openai(all_sents, batch_size=32)

for s, key, a, f, o in zip(all_sents, mapping, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:18s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
