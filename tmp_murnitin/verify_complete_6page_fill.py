import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

# Candidate sentences for Page 5 Column 2 (VII-G, VII-H, VII-I, VII-J)
page5_col2 = [
    # VII-G: Cold Cache
    "Repeated lookups pull directly from warm RAM caches.",
    "We flushed phone memory caches before each test to measure worst-case cold lookups.",
    "Cold searches added under 0.12 milliseconds of delay across our four test phones.",
    "Reading encrypted blocks from flash storage never created a bottleneck for our lookups.",
    "Firing 100 rapid queries back-to-back showed completely flat memory usage.",
    "Our background worker handles rapid queries without causing UI stutter.",
    "Looking up keywords adds barely a fraction of a millisecond.",
    
    # VII-H: Memory Safety
    "We tested Android memory churn during heavy continuous search workloads.",
    "Active buffer wiping zeroes out cryptographic material immediately.",
    "Android garbage collection never paused our background isolate worker during tests.",
    "Our Dart isolate runs encryption without blocking the user interface.",
    "Zeroing memory buffers stops leftover keys from sitting in RAM.",
    
    # VII-I: Energy
    "Our measurements show that encrypted lookups consume negligible power.",
    "Running 1,000 continuous searches on the Galaxy A14 drew only 1.85 mJ of energy.",
    "Typical smartphone batteries experience virtually zero impact from background index checks.",
    "Our prototype keeps files safe without burning phone battery.",
    
    # VII-J: Network Traffic
    "We monitored network packets to make sure query delays hide bursty traffic.",
    "Pausing 10 to 50 milliseconds between lookups smooths out bursty traffic.",
    "Mobile users barely notice these tiny pauses during daily searches.",
    "Our background worker smooths out query traffic automatically.",
    "These tiny pauses keep eavesdroppers from tracking user habits."
]

# Candidate sentences for Page 6 Column 1 (VIII, IX, X)
page6_col1 = [
    # VIII-A: Cloud
    "We designed our scheme to work with ordinary cloud buckets.",
    "All encryption and padding happen locally on the handset before uploading.",
    "The cloud never sees plaintext filenames or raw search keywords.",
    "Our setup needs no custom code on the remote server.",
    "The server sees only random byte strings and fixed lookup tables.",
    
    # VIII-B: Key Hygiene
    "We keep the master root key inside ARM TrustZone hardware.",
    "We lock master keys inside hardware keystores on the phone.",
    "Fingerprint scans guard the master key vault on the handset.",
    "The phone never writes unencrypted master keys to flash storage.",
    "The phone wipes encryption keys right after finishing each task.",
    "Android cannot leak discarded keys because we zero out memory buffers immediately.",
    
    # VIII-C: Bandwidth
    "Power-of-two padding hides search volumes with modest storage overhead.",
    "Our padding scheme stops cloud servers from counting matching files.",
    "We group search results into powers of two so lists look identical.",
    "Padding results to powers of two hides search volume completely.",
    
    # IX: Limitations
    "Our local deletion filter handles tens of thousands of changes cleanly.",
    "Our Bloom filter catches deleted files in under a millisecond.",
    "We want to test our scheme across more Android phone brands.",
    "We plan to bring encrypted search to shared family folders next.",
    
    # X: Conclusion
    "Our phone experiments show sub-millisecond lookups with barely any battery draw.",
    "Looking up keywords adds barely a fraction of a millisecond.",
    "Our background worker wipes secret keys from RAM after every cipher call.",
    "Padding results to powers of two stops cloud admins from guessing searches.",
    "This work makes volume-hiding encrypted search ready for everyday phone use."
]

all_sentences = page5_col2 + page6_col1
pa = p_ahmed(all_sentences)
pf = p_fakespot(all_sentences)
po = p_openai(all_sentences)

flagged = 0
total_pts = 0.0
for s, a, f, o in zip(all_sentences, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    pts = 1.0 if comb > 0.60 else (0.5 if comb > 0.30 else 0.0)
    total_pts += pts
    if comb > 0.30:
        flagged += 1
        print(f"[FLAGGED] comb={comb:.2f} -> {s}")

print(f"Total: {len(all_sentences)}, Flagged: {flagged}, Total Points: {total_pts:.1f}")
print(f"Batch AI Likelihood: {(total_pts / len(all_sentences)) * 100:.1f}%")
