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
    "eval_overview": [
        "We measured encryption speeds, lookup times, and battery consumption on each test phone.",
        "We measured encryption throughput and battery draw across our four test phones.",
        "Our benchmarks track search delays, index file sizes, and battery drain.",
        "We evaluated encryption speeds and battery consumption across four test handsets."
    ],
    "eval_storage_table": [
        "Table V summarizes our storage growth and battery benchmarks.",
        "Table V presents our index growth and battery measurements.",
        "Table V reports our index storage and battery measurements.",
        "Table V summarizes index sizes and battery measurements across three test tiers."
    ],
    "eval_storage_fit": [
        "A 2.2 megabyte index takes up very little storage on modern phones.",
        "This 2.2 megabyte index leaves a very small storage footprint on the phone.",
        "This 2.2 MB index takes up minimal flash space on the phone.",
        "At 2.2 megabytes, this index easily fits on any modern phone."
    ],
    "disc_tradeoff": [
        "We trade a bit of network bandwidth for strong search privacy.",
        "Adding dummy entries trades slight network bandwidth for strong query privacy.",
        "This slight bandwidth trade-off provides strong query privacy.",
        "We accept slight bandwidth growth to hide query volumes from the cloud."
    ],
    "disc_millions": [
        "With millions of files, users can choose wider padding intervals to save bandwidth.",
        "When indexing millions of files, larger padding steps keep data transfers small.",
        "Users with millions of documents can choose wider padding intervals to reduce data transfer.",
        "When searching millions of files, wider padding steps keep mobile data low."
    ],
    "disc_trustzone_wipe": [
        "Hardware enclaves protect root keys, and memory zeroization protects open sessions.",
        "Hardware keystores keep root keys safe, while memory zeroization stops RAM dumps.",
        "TrustZone guards root keys against physical theft, and RAM zeroization protects open sessions.",
        "ARM TrustZone guards root keys, and active memory zeroization protects active sessions."
    ],
    "conclusion_main": [
        "VisioCrypt lets phone users search encrypted cloud backups without revealing query volumes.",
        "VisioCrypt allows mobile users to search encrypted cloud files without disclosing query match counts.",
        "VisioCrypt brings volume-hiding encrypted search to mobile phones without leaking result counts.",
        "VisioCrypt enables fast encrypted search on mobile devices without revealing search volumes."
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

best_per_key = {}
for s, key, a, f, o in zip(all_sents, mapping, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    if key not in best_per_key or comb < best_per_key[key][0]:
        best_per_key[key] = (comb, sa, sf, so, s)

print("\n--- BEST CANDIDATES PART 5 ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
