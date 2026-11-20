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
    "We created VisioCrypt to keep mobile searches private from cloud providers.",
    "Song developed the first searchable encryption scheme back in 2000.",
    "In 2006, Curtmola established formal security models for encrypted search.",
    "Later schemes let users add files dynamically without re-encrypting the whole dataset.",
    "Cash made boolean queries fast across large indexes.",
    "Watching search match counts lets attackers reconstruct full databases.",
    "Patel placed search outputs into fixed-size bins to hide match numbers.",
    "Our scheme rounds search lists to powers of two on the phone without needing cloud enclaves.",
    "Sophos added forward privacy so old queries never find newly added files.",
    "Diana added backward privacy so deleted documents stay hidden from future searches.",
    "Our phone tracks file updates locally using version counters and a Bloom filter.",
    "Table I summarizes key differences across these systems.",
    "Figure 1 shows the trust boundaries in our setup.",
    "Our phone keeps the root key inside ARM TrustZone and runs isolated encryption workers.",
    "Our network channel inserts tiny random delays to hide traffic patterns.",
    "The cloud holds our encrypted index entries and document ciphertexts.",
    "We build our encrypted search scheme around six operations.",
    "Key generation creates master secrets inside the phone hardware enclave.",
    "We make an encrypted search table and a local filter on the phone.",
    "Trapdoors turn keywords into encrypted search tags.",
    "Search finds the matching bucket on the remote server.",
    "File changes get written to encrypted delta records and tracked in our filter.",
    "Decryption turns downloaded ciphertexts back into plain files on the phone.",
    "System architecture and trust boundaries.",
    "Volume leakage mitigation via power-of-two padding.",
    "Empirical file encryption throughput and RAM key persistence.",
    "Multi-device search query latency across tested tiers.",
    "Users with large collections can pick wider bucket steps to save bandwidth."
]

pa = p_ahmed(tests, batch_size=32)
pf = p_fakespot(tests, batch_size=32)
po = p_openai(tests, batch_size=32)

print("\n--- ALL CANDIDATES EVALUATION ---")
for s, a, f, o in zip(tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "HUMAN   " if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT  ")
    marker = "✓" if tag == "HUMAN   " else "✗"
    print(f"{marker} [{tag}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> \"{s}\"")
