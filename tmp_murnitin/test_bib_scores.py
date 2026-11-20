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

bib_tests = [
    "[1] R. Shokri et al., Membership inference attacks on machine learning, IEEE S&P, 2017.",
    "[1] R. Shokri, M. Stronati, C. Song, and V. Shmatikov, Membership inference attacks against machine learning models, in IEEE S&P, 2017.",
    "[2] N. Carlini et al., Extracting training data from large language models, USENIX Security, 2021.",
    "[3] D. Song, D. Wagner, and A. Perrig, Practical techniques for searches on encrypted data, IEEE S&P, 2000.",
    "[4] R. Curtmola, J. Garay, S. Kamara, and R. Ostrovsky, Searchable symmetric encryption: Improved definitions and efficient constructions, ACM CCS, 2006.",
    "[5] S. Kamara, C. Papamanthou, and T. Roeder, Dynamic searchable symmetric encryption, ACM CCS, 2012.",
    "[6] D. Cash et al., Highly-scalable searchable symmetric encryption with support for boolean queries, CRYPTO, 2013."
]

pa = p_ahmed(bib_tests, batch_size=32)
pf = p_fakespot(bib_tests, batch_size=32)
po = p_openai(bib_tests, batch_size=32)

for s, a, f, o in zip(bib_tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    print(f"[{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
