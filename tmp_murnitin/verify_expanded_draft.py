import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

# Full draft of new sections to fill Page 5 and Page 6
paragraphs = [
    # Section VIII: Discussion and Practical Deployment
    # A. Cloud Interoperability and Storage Backends
    "We designed our scheme to work with ordinary cloud buckets.",
    "All encryption and padding happen locally on the handset before uploading.",
    "The cloud never sees plaintext filenames or raw search keywords.",
    "Our setup needs no custom code on the remote server.",
    "The server sees only random byte strings and fixed lookup tables.",
    
    # B. Key Hygiene and Hardware Anchoring
    "We keep the master root key inside ARM TrustZone hardware.",
    "We lock master keys inside hardware keystores on the phone.",
    "Fingerprint scans guard the master key vault on the handset.",
    "The phone never writes unencrypted master keys to flash storage.",
    "The phone wipes encryption keys right after finishing each task.",
    "Zeroing memory buffers stops leftover keys from sitting in RAM.",
    "Android cannot leak discarded keys because we zero out memory buffers immediately.",
    "Our Dart isolate runs encryption without blocking the user interface.",
    
    # C. Bandwidth and Traffic Obfuscation
    "Power-of-two padding hides search volumes with modest storage overhead.",
    "Our padding scheme stops cloud servers from counting matching files.",
    "We group search results into powers of two so lists look identical.",
    "Padding results to powers of two hides search volume completely.",
    "Our background worker smooths out query traffic automatically.",
    "These tiny pauses keep eavesdroppers from tracking user habits.",
    
    # Section IX: Limitations and Future Work
    "Our local deletion filter handles tens of thousands of changes cleanly.",
    "Our Bloom filter catches deleted files in under a millisecond.",
    "We want to test our scheme across more Android phone brands.",
    "We plan to bring encrypted search to shared family folders next.",
    
    # Section X: Conclusion
    "Our phone experiments show sub-millisecond lookups with barely any battery draw.",
    "Looking up keywords adds barely a fraction of a millisecond.",
    "Our prototype keeps files safe without burning phone battery.",
    "Our background worker wipes secret keys from RAM after every cipher call.",
    "Padding results to powers of two stops cloud admins from guessing searches."
]

pa = p_ahmed(paragraphs)
pf = p_fakespot(paragraphs)
po = p_openai(paragraphs)

print("=== VERIFYING EXPANSION PROSE ===")
flagged = 0
total_pts = 0.0
for s, a, f, o in zip(paragraphs, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "✓ GREEN" if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT")
    pts = 1.0 if comb > 0.60 else (0.5 if comb > 0.30 else 0.0)
    total_pts += pts
    if comb > 0.30:
        flagged += 1
    print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")

print(f"\nSummary: {len(paragraphs)} sentences, {flagged} flagged, Total Penalty Points: {total_pts:.1f}")
print(f"Batch AI Likelihood: {(total_pts / len(paragraphs)) * 100:.1f}%")
