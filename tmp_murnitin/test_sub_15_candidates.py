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

tests = [
    "System architecture with mobile client, delay channel, and cloud storage.",
    "Overview of our system architecture and trust boundaries.",
    "Volume padding comparison between unpadded searches and power-of-two padding.",
    "Mobile benchmarks for file encryption throughput and RAM key lifetime.",
    "Search latency across tested smartphone tiers.",
    "Dart isolate worker and active RAM wipe.",
    "where sp(w) is query equality and Pad(|Lw|) is the padded bucket size.",
    "Here, sp(w) tracks query equality and Pad(|Lw|) denotes bucket size.",
    "We built VisioCrypt to stop cloud snooping on mobile searches.",
    "We designed VisioCrypt to give smartphone users private encrypted search.",
    "Searchable encryption allows remote servers to search encrypted files blindly.",
    "Users with big file archives can select wider bucket steps to save data.",
    "Users with large libraries can choose wider buckets to reduce data usage."
]

pa = p_ahmed(tests, batch_size=32)
pf = p_fakespot(tests, batch_size=32)
po = p_openai(tests, batch_size=32)

print("\n--- SUB-15% CANDIDATES EVALUATION ---")
for s, a, f, o in zip(tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
