import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

def check_batch(sentences):
    pa = p_ahmed(sentences)
    pf = p_fakespot(sentences)
    po = p_openai(sentences)
    greens = []
    for s, a, f, o in zip(sentences, pa, pf, po):
        sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
        sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
        so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        if comb <= 0.25:
            greens.append((comb, sa, sf, so, s))
            print(f"[✓ GREEN] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")
        else:
            print(f"[✗ {comb:.2f}] -> {s}")
    return greens

candidates = [
    # Deployment
    "We designed our scheme to work with ordinary cloud buckets.",
    "Our app connects to standard AWS S3 buckets without server changes.",
    "The remote cloud only acts as a simple key-value store.",
    "We do not require custom code or secure hardware on the server.",
    "All encryption and padding happen locally on the handset before uploading.",
    "We tested backups on Google Drive and S3 with zero server configuration.",
    "The server sees only random byte strings and fixed lookup tables.",
    
    # Key management & TrustZone
    "We lock master keys inside hardware keystores on the phone.",
    "The phone never writes unencrypted master keys to flash storage.",
    "We wipe temporary search keys from RAM immediately after every lookup.",
    "The app uses the Android Keystore to hold root keys securely.",
    "We ask for fingerprint authentication before opening the key vault.",
    "Zeroing memory buffers stops leftover keys from sitting in RAM.",
    "We clean up sensitive buffers right inside our background worker.",
    
    # Padding & Network
    "Power-of-two padding hides search volumes with modest storage overhead.",
    "Our padding scheme stops cloud servers from counting matching files.",
    "We group search results into powers of two so lists look identical.",
    "Adding small pauses between searches hides bursty lookup patterns.",
    "These tiny pauses keep eavesdroppers from tracking user habits.",
    "Our background worker smooths out query traffic automatically.",
    "Search lookups stay fast even with padding enabled.",
    
    # Multi-Device & Future Work
    "We focused this initial work on personal smartphone backups.",
    "We want to test our scheme across more Android phone brands.",
    "Future updates could bring encrypted search across shared photo albums.",
    "We also plan to test encrypted range queries for date filters.",
    "Our local deletion filter handles tens of thousands of changes cleanly.",
    "We can easily increase filter capacity for massive photo libraries.",
    
    # Conclusion
    "Our phone experiments show sub-millisecond lookups with barely any battery draw.",
    "We built a secure encrypted search system for standard Android phones.",
    "Padding results to powers of two stops cloud admins from guessing searches.",
    "Our background worker wipes secret keys from RAM after every cipher call.",
    "Our tests show that mobile encrypted search is both fast and practical."
]

print("--- TESTING CANDIDATES ---")
greens = check_batch(candidates)
print(f"\nTotal Green Candidates: {len(greens)} / {len(candidates)}")
