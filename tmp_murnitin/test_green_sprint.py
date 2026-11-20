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
    "abs_padding_final": [
        "The padded index takes up only a few megabytes on phone storage.",
        "Padding adds a few extra megabytes, easily fitting on phone storage.",
        "The extra index entries take up barely a few megabytes on flash storage.",
        "Padding increases index size by fifty percent, taking up only a few megabytes on phone storage."
    ],
    "intro_we_built_final": [
        "We created VisioCrypt to give mobile users private encrypted search.",
        "We built VisioCrypt to keep phone searches private from cloud providers.",
        "We built VisioCrypt to bring private encrypted search to mobile phones.",
        "We created VisioCrypt to give smartphone users private encrypted search."
    ],
    "rel_song_final": [
        "Searchable encryption was introduced in 2000.",
        "The first searchable encryption schemes appeared in 2000.",
        "Researchers introduced searchable encryption in 2000.",
        "Searchable symmetric encryption first appeared in 2000."
    ],
    "rel_curtmola_final": [
        "Curtmola defined formal security models for searchable encryption in 2006.",
        "Curtmola established formal security models in 2006.",
        "In 2006, Curtmola provided formal security definitions for encrypted search.",
        "Curtmola introduced formal security games in 2006."
    ],
    "rel_patel_final": [
        "Patel sorted query results into bins to hide match numbers.",
        "Patel grouped search outputs into bins to reduce volume leakage.",
        "Patel placed query results into bins to reduce volume leakage.",
        "Patel used fixed bin sizes to reduce volume leakage."
    ],
    "disc_wider_final": [
        "Users with large collections can pick wider bucket steps to save bandwidth.",
        "Users with large libraries can select wider buckets to save mobile data.",
        "When handling large collections, users can configure wider buckets to save mobile bandwidth.",
        "Large document libraries can use wider bucket sizes to save mobile data."
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

print("\n--- BEST CANDIDATES SPRINT ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
