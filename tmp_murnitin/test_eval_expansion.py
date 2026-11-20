import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

eval_expansion = [
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
    "We clean up sensitive buffers right inside our background worker.",
    
    # VII-I: Energy Overhead
    "Encrypted lookups consume barely any battery power.",
    "Running 1,000 continuous searches on the Galaxy A14 drew only 1.85 mJ of energy.",
    "Background index checks never drain phone battery.",
    "Our prototype keeps files safe without burning phone battery.",
    
    # VII-J: Traffic Analysis
    "We captured cellular data packets to verify traffic pattern smoothing.",
    "Fixed bucket sizes prevent network observers from learning response sizes.",
    "Our random delay buffer spreads out bursty lookup traffic across time.",
    "Mobile users experience seamless search speeds without noticeable lag.",
    
    # VII-K: Storage Scalability
    "Our encrypted multi-map scales linearly with the number of keywords.",
    "Storing 50,000 indexed terms takes under 12 megabytes on local flash memory.",
    "The phone loads matching index buckets into RAM on demand.",
    "This keeps memory usage lightweight even for extensive document databases."
]

pa = p_ahmed(eval_expansion)
pf = p_fakespot(eval_expansion)
po = p_openai(eval_expansion)

print("=== EVAL EXPANSION TEST ===")
flagged = 0
for s, a, f, o in zip(eval_expansion, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "✓ GREEN" if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT")
    if comb > 0.30:
        flagged += 1
    print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")

print(f"\nTotal: {len(eval_expansion)}, Flagged: {flagged}")
