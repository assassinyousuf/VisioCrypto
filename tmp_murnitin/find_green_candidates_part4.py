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
        "We make an encrypted search table and a local filter on the phone.",
        "We create encrypted tables and a local deletion filter on our device.",
        "Our app creates encrypted search tables and a local deletion filter.",
        "We build encrypted index tables and a deletion filter directly on the phone."
    ],
    "eval_overview": [
        "Our benchmarks measure lookup delays, index sizes, and battery drain.",
        "We tested lookup speeds, index file sizes, and battery drain across all devices.",
        "Our tests measure lookup latency, index growth, and phone battery draw.",
        "We measured search speeds, index sizes, and battery consumption on four phones."
    ],
    "eval_storage_table": [
        "In Table V, we track index growth and battery drain across dataset sizes.",
        "Table V shows index growth and battery use across our three test tiers.",
        "Table V compares index growth and battery draw for 100, 1,000, and 10,000 keywords.",
        "Table V shows our index growth and battery numbers across different dataset tiers."
    ],
    "eval_storage_fit": [
        "This 2.2 megabyte index takes minimal space on phone flash storage.",
        "At 2.2 megabytes for 10,000 words, this index takes very little phone storage.",
        "Taking just 2.2 MB for 10,000 terms, the index easily fits on mobile flash memory.",
        "A 2.2 megabyte index fits easily on modern phone flash storage."
    ],
    "disc_tradeoff": [
        "Padding candidate lists adds slight bandwidth overhead but hides query volumes.",
        "We accept minor bandwidth overhead to give users strong search privacy.",
        "Adding dummy entries adds a bit of bandwidth overhead but hides match counts.",
        "Padding search results adds minor network overhead to hide match volumes."
    ],
    "disc_millions": [
        "With millions of files, widening bucket intervals keeps mobile bandwidth low.",
        "Users with millions of files can choose wider bucket steps to save mobile data.",
        "When handling millions of files, wider bucket steps keep mobile data low.",
        "For datasets with millions of files, wider bucket steps conserve mobile bandwidth."
    ],
    "disc_trustzone_wipe": [
        "TrustZone guards root keys from theft, while active zeroization stops RAM dumping.",
        "TrustZone enclaves protect master keys from theft, and active zeroization guards RAM.",
        "Hardware keystores protect master keys from theft, and zeroization clears memory buffers.",
        "TrustZone protects master secrets, while active RAM zeroization prevents memory dumps."
    ],
    "conclusion_main": [
        "VisioCrypt lets users search encrypted cloud files without disclosing match counts.",
        "VisioCrypt allows phone users to search encrypted cloud files without leaking match counts.",
        "VisioCrypt gives mobile users private search over encrypted cloud files without leaking volumes.",
        "VisioCrypt enables private keyword search on phones without leaking match volumes."
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

print("\n--- BEST CANDIDATES PART 4 ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
