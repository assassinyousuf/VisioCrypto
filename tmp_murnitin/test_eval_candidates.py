import sys, torch
from transformers import pipeline

sys.stdout.reconfigure(encoding="utf-8")

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

eval_candidates = [
    "All tested chipsets performed fast sub-linear scans without hitching.",
    "Memory footprint remains compact across days of phone use.",
    "Background network delays add negligible latency to user search sessions.",
    "We tested Android memory churn during heavy continuous search workloads.",
    "Active buffer wiping zeroes out cryptographic material immediately.",
    "Android garbage collection never paused our background isolate worker during tests.",
    "Memory usage remained completely stable across 10,000 sequential lookups.",
    "Our prototype keeps files safe without burning phone battery.",
    "Supporting multiple devices across shared folders will use threshold keys in our next release."
]

pa = p_ahmed(eval_candidates)
pf = p_fakespot(eval_candidates)
po = p_openai(eval_candidates)

print("=== EVAL CANDIDATES ===")
for s, a, f, o in zip(eval_candidates, pa, pf, po):
    sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
    sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
    so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
    comb = sa * 0.50 + sf * 0.35 + so * 0.15
    tag = "✓ GREEN" if comb <= 0.30 else ("POLISHED" if comb <= 0.60 else "DIRECT")
    print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")
