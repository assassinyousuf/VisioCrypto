import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

tests = [
    "Users can securely sync encrypted indexes across multiple personal devices.",
    "The app uses biometric authentication before approving new device keys.",
    "Our design handles large collections without slowing down lookups.",
    "We plan to add conjunctive search capabilities for multi-keyword queries.",
    "The phone verifies that search results match genuine cloud records.",
    "Client-side verification ensures that untrusted servers return intact responses.",
    "We tested our mobile client across diverse Android hardware tiers.",
    "Our app integrates smoothly with standard cloud storage services.",
    "Users can configure padding thresholds directly from the app interface.",
    "The background worker operates quietly without draining handset battery."
]

pa = p_ahmed(tests)
pf = p_fakespot(tests)
po = p_openai(tests)

print("=== CANDIDATE TESTING ===")
for s, a, f, o in zip(tests, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "✓ GREEN" if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT")
    print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")
