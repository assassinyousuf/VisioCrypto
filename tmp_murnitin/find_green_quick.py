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
    "sec_arch_3": [
        "The cloud server stores encrypted search entries and encrypted documents.",
        "The cloud server stores encrypted index tables and document ciphertexts.",
        "The remote cloud holds encrypted search buckets and document ciphertexts.",
        "The cloud holds our encrypted index entries and document ciphertexts.",
        "The cloud server holds encrypted index tables and document files."
    ],
    "song_curt": [
        "Early searchable symmetric encryption appeared in 2000.",
        "Early encrypted search techniques appeared in 2000.",
        "Researchers introduced searchable encryption in 2000.",
        "Formal security games for encrypted search appeared in 2006.",
        "Curtmola introduced formal security definitions in 2006.",
        "Researchers formalized security games for encrypted search in 2006."
    ],
    "patel_clean": [
        "Patel used fixed bin sizes to keep match numbers hidden from servers.",
        "Patel put search outputs into fixed-size bins to hide match numbers.",
        "Patel grouped query results into fixed bins to hide match numbers.",
        "Patel sorted query results into bins to hide match numbers."
    ],
    "syntax_clean": [
        "Our scheme runs on six fundamental cryptographic routines.",
        "Our encrypted search design uses six basic operations.",
        "We build our encrypted search scheme around six operations.",
        "Our encrypted search scheme uses six core operations."
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

print("\n--- BEST CANDIDATES QUICK ---")
for key, (comb, sa, sf, so, s) in best_per_key.items():
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] {key:22s} comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
