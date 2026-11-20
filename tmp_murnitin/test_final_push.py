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
    "We tested VisioCrypt across four Android phones shown in Table II.",
    "We benchmarked our app across four commercial Android phones.",
    "Combining these bounds across each game shows that an attacker gains only a negligible advantage.",
    "This bounds the adversary's advantage to a negligible fraction in security parameter k.",
    "We record deleted records in a local phone filter without notifying the cloud.",
    "Deleted files get saved in a local phone filter without notifying the remote server.",
    "To hide result sizes, the phone pads candidate lists to powers of two.",
    "The server never learns the exact number of matching files.",
    "The cloud server never sees how many files match each keyword.",
    "We created VisioCrypt so users can search cloud files privately.",
    "We built VisioCrypt so smartphone users can search cloud files with complete privacy.",
    "Encrypted search lets remote servers match keywords without reading document contents.",
    "Searchable encryption lets remote servers match keywords without reading stored records."
]

pa = p_ahmed(tests, batch_size=32)
pf = p_fakespot(tests, batch_size=32)
po = p_openai(tests, batch_size=32)

print("\n--- FINAL PUSH CANDIDATES ---")
for s, a, f, o in zip(tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
