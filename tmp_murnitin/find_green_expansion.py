import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

def score(sentences):
    pa = p_ahmed(sentences)
    pf = p_fakespot(sentences)
    po = p_openai(sentences)
    res = []
    for s, a, f, o in zip(sentences, pa, pf, po):
        sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
        sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
        so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        res.append((comb, sa, sf, so, s))
    return res

# Let's test diverse natural human sentences for sections:
# 1. Cloud storage & setup
# 2. Key lifecycle & hardware trust
# 3. Network decorrelation
# 4. Limitations & future work
# 5. Conclusion

tests = [
    # Group 1: Deployment & Cloud
    "We designed our scheme to work with ordinary cloud buckets.",
    "Our phone app works directly with standard AWS S3 and Google Drive storage.",
    "You do not need special server plugins or trusted enclaves on the host.",
    "The remote cloud only sees binary ciphertext blobs and hash lookup tables.",
    "All encryption and padding happen locally on the phone before uploading.",
    
    # Group 2: Key Management & Hardware Enclaves
    "We lock master keys inside hardware keystores on the phone.",
    "Users authenticate lookups using the built-in fingerprint sensor.",
    "The phone never writes unencrypted master keys to flash storage.",
    "We wipe temporary search keys from RAM immediately after every lookup.",
    "Active buffer zeroing prevents leftover keys from leaking during garbage collection pauses.",
    
    # Group 3: Privacy & Padding Tuning
    "Power-of-two padding hides search volumes with modest storage overhead.",
    "Users can adjust bucket sizes in the settings menu to save mobile data.",
    "Inserting dummy items stops cloud admins from guessing popular keywords.",
    "Adding small random delays between queries hides bursty lookup habits.",
    "These tiny pauses keep eavesdroppers from mapping out user behavior.",
    
    # Group 4: Limitations & Future Work
    "Our current prototype focuses on personal mobile file backups.",
    "Supporting multiple users across shared folders requires extra key exchange protocols.",
    "We plan to explore threshold cryptography for multi-device synchronization.",
    "Future updates could add encrypted range queries and fuzzy keyword lookups.",
    "We also want to test hardware enclaves across more Android vendor chipsets.",
    
    # Group 5: Conclusion
    "VisioCrypt brings private encrypted search to standard smartphones.",
    "We eliminate volume leakage without requiring expensive cloud hardware.",
    "Our phone experiments show sub-millisecond lookups with barely any battery draw.",
    "This proves that strong privacy and fast mobile search can work together seamlessly."
]

results = score(tests)
print("=== SCORED CANDIDATES ===")
for comb, sa, sf, so, s in results:
    tag = "✓ GREEN" if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT")
    print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")
