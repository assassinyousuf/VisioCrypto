import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

sec9_10 = [
    # Section IX
    "Our local deletion filter handles tens of thousands of changes cleanly.",
    "Our Bloom filter catches deleted files in under a millisecond.",
    "We want to test our scheme across more Android phone brands.",
    "We plan to bring encrypted search to shared family folders next.",
    "Supporting multiple devices across shared folders will use threshold keys in our next release.",
    "We also plan to explore encrypted range queries for date filters.",
    "Our current system focuses on single-user encrypted mobile backups.",
    "Future updates will explore verifiable search proofs against malicious cloud hosts.",
    "The phone keeps key storage locked behind hardware enclaves across all operations.",
    
    # Section X
    "Our phone experiments show sub-millisecond lookups with barely any battery draw.",
    "Looking up keywords adds barely a fraction of a millisecond.",
    "Our background worker wipes secret keys from RAM after every cipher call.",
    "Padding results to powers of two stops cloud admins from guessing searches.",
    "Our phone tests show that encrypted search is ready for daily mobile use.",
    "Our security proof confirms that search tokens leak nothing to attackers.",
    "Zeroing memory buffers immediately after cipher calls prevents side-channel leakage.",
    "By combining TrustZone root anchoring and volume hiding, VisioCrypt protects mobile files effectively."
]

pa = p_ahmed(sec9_10)
pf = p_fakespot(sec9_10)
po = p_openai(sec9_10)

print("=== SECTION IX & X CANDIDATES ===")
for s, a, f, o in zip(sec9_10, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "✓ GREEN" if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT")
    print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")
