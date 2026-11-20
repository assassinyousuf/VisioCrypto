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
    "eval_storage_table": [
        "Table V summarizes our benchmark results.",
        "Table V lists our test results.",
        "Table V shows our test numbers.",
        "We list our storage and energy numbers in Table V.",
        "Our storage and power results are listed in Table V."
    ],
    "eval_storage_fit": [
        "The index fits easily on flash storage.",
        "This index easily fits on flash memory.",
        "This index easily fits on the phone.",
        "A 2.2 megabyte file easily fits on modern phones.",
        "Storing 2.2 megabytes of index data takes barely any flash space."
    ],
    "disc_tradeoff": [
        "Padding results trades a bit of extra bandwidth for strong search privacy.",
        "We trade a bit of extra network data for strong search privacy.",
        "Padding results uses a little extra bandwidth to protect search privacy.",
        "We send a little extra data to protect search privacy."
    ],
    "disc_millions": [
        "Users with millions of files can pick wider bucket steps to save mobile data.",
        "With millions of files, picking wider bucket steps keeps mobile data low.",
        "When handling millions of files, users can choose wider intervals to save bandwidth.",
        "Users with large collections can pick wider bucket steps to save mobile data."
    ],
    "disc_trustzone_wipe": [
        "Hardware enclaves protect master keys, while zeroization clears active RAM.",
        "Hardware keystores keep root keys safe, while active zeroization clears RAM.",
        "Hardware enclaves protect master secrets, and zeroization clears memory buffers.",
        "ARM hardware locks root secrets, while active RAM zeroization protects open sessions."
    ],
    "conclusion_main": [
        "VisioCrypt lets users search encrypted files without revealing search counts.",
        "VisioCrypt lets mobile users search encrypted files without leaking search volumes.",
        "VisioCrypt brings private search to phones without leaking result counts.",
        "VisioCrypt brings private encrypted search to mobile phones."
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

print("\n--- BEST CANDIDATES PART 6 ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
