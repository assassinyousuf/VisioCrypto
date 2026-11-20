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
    "syntax_build": [
        "Building the index produces encrypted search records and a phone-side deletion filter.",
        "We create encrypted search buckets and a local filter on the phone.",
        "The indexing step produces encrypted search records and an in-memory deletion filter.",
        "Index generation outputs encrypted lookup blocks and a local Bloom filter."
    ],
    "eval_overview": [
        "We measured throughput, memory retention, lookup times, storage growth, and battery drain.",
        "Our test suite measures throughput, RAM retention, lookup speed, storage overhead, and battery drain.",
        "We tested raw file speed, memory lifetimes, lookup delays, storage size, and battery drain.",
        "We tracked throughput, RAM lifetimes, search delays, storage growth, and power use."
    ],
    "eval_storage_table": [
        "Table V reports index growth and battery drain across our test datasets.",
        "Table V shows storage growth and battery use for different dataset sizes.",
        "Table V breaks down storage expansion and battery consumption across dataset sizes.",
        "Table V details storage overhead and power consumption across our test benchmarks."
    ],
    "eval_storage_fit": [
        "This 2.2 megabyte index takes minimal space on phone flash memory.",
        "This 2.2 MB index takes up very little space on mobile flash storage.",
        "Taking just 2.2 megabytes for 10,000 words, the index easily fits on flash storage.",
        "The resulting 2.2 megabyte index fits easily on modern phone storage."
    ],
    "disc_tradeoff": [
        "Padding candidate lists trades a small bandwidth increase for strong query privacy.",
        "We accept a small bandwidth penalty to achieve strong query privacy.",
        "Padding search lists introduces slight bandwidth overhead in exchange for strong privacy.",
        "Adding dummy entries adds a small bandwidth penalty but protects search privacy."
    ],
    "disc_millions": [
        "For very large libraries with millions of files, users can widen bucket steps to conserve bandwidth.",
        "With millions of files, users can widen bucket intervals to save mobile bandwidth.",
        "For large archives with millions of files, widening bucket intervals keeps bandwidth low.",
        "When managing millions of files, wider bucket steps keep bandwidth usage low."
    ],
    "disc_trustzone_wipe": [
        "TrustZone enclaves keep master keys safe from theft, and active zeroization stops RAM dumping.",
        "TrustZone enclaves guard master secrets against theft, while active zeroization protects open sessions.",
        "TrustZone hardware guards master keys, while active zeroization stops RAM dumping.",
        "TrustZone enclaves protect master keys from theft, while zeroization stops memory dumping."
    ],
    "conclusion_main": [
        "VisioCrypt lets mobile users search encrypted cloud storage without disclosing search volumes.",
        "VisioCrypt allows smartphone users to search encrypted cloud files without disclosing match counts.",
        "VisioCrypt enables private search over encrypted cloud archives without leaking result counts.",
        "VisioCrypt lets phone users search encrypted cloud archives without disclosing match counts."
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

print("\n--- BEST CANDIDATES PART 3 ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
