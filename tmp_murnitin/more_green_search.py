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
    for s, a, f, o in zip(sentences, pa, pf, po):
        sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
        sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
        so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        tag = "✓ GREEN" if comb <= 0.25 else ("POLISHED" if comb <= 0.60 else "DIRECT")
        print(f"[{tag:8s}] comb={comb:.2f} (a={sa:.2f}, f={sf:.2f}, o={so:.2f}) -> {s}")

more_candidates = [
    # Deployment details
    "We store encrypted files in simple S3 buckets.",
    "Standard cloud services like Google Drive work without any modification.",
    "The phone encrypts every record before sending network packets.",
    "The cloud never sees plaintext filenames or raw search keywords.",
    "Our setup needs no custom code on the remote server.",
    
    # Key security details
    "We keep the master root key inside ARM TrustZone hardware.",
    "The phone wipes encryption keys right after finishing each task.",
    "Fingerprint scans guard the master key vault on the handset.",
    "Android cannot leak discarded keys because we zero out memory buffers immediately.",
    "Our Dart isolate runs encryption without blocking the user interface.",
    
    # Performance & network details
    "Looking up keywords adds barely a fraction of a millisecond.",
    "Padding results to powers of two hides search volume completely.",
    "Tiny random delays between searches smooth out network bursts.",
    "Our Bloom filter catches deleted files in under a millisecond.",
    "The local deletion table uses only a few kilobytes of RAM.",
    
    # Conclusion & future outlook
    "We proved that private mobile search is fast and practical.",
    "Our prototype keeps files safe without burning phone battery.",
    "We plan to bring encrypted search to shared family folders next.",
    "Our security analysis confirms that search tokens leak zero plaintext.",
    "This work makes volume-hiding encrypted search ready for everyday phone use."
]

check_batch(more_candidates)
