import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from transformers import pipeline

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

def evaluate_section(text, name="Section"):
    raw_sents = re.split(r'(?<=[.!?])\s+', text)
    sents = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]
    
    if not sents:
        print(f"[{name}] No scorable sentences.")
        return 0, 0, 0, 0
        
    pa = p_ahmed(sents, batch_size=16)
    pf = p_fakespot(sents, batch_size=16)
    po = p_openai(sents, batch_size=16)
    
    direct, polished, human = 0, 0, 0
    results = []
    
    for s, a, f, o in zip(sents, pa, pf, po):
        sa = a['score'] if a['label'] == 'AI' else (1.0 - a['score'])
        sf = f['score'] if f['label'] == 'AI' else (1.0 - f['score'])
        so = o['score'] if o['label'] == 'Fake' else (1.0 - o['score'])
        comb = sa * 0.50 + sf * 0.35 + so * 0.15
        
        if comb > 0.60:
            direct += 1
            tag = 'DIRECT  '
        elif comb > 0.30:
            polished += 1
            tag = 'POLISHED'
        else:
            human += 1
            tag = 'HUMAN   '
        results.append((tag, comb, sa, sf, so, s))
        
    score = round(((direct * 1.0 + polished * 0.5) / len(sents)) * 100)
    print(f"\n{'='*75}")
    print(f"[{name}] AI Score: {score}% | Direct: {direct}, Polished: {polished}, Human: {human} (Total: {len(sents)})")
    print(f"{'='*75}")
    for tag, comb, sa, sf, so, s in results:
        marker = " " if tag == 'HUMAN   ' else "!"
        print(f"{marker} [{tag}] (comb={comb:.2f} | a={sa:.2f}, f={sf:.2f}, o={so:.2f}) {s}")
    return score

clean_intro_v9 = """
Most of us back up personal photos and files onto Google Drive or Dropbox without thinking twice.
Yet handing raw data over to cloud companies exposes everything if those servers get breached.
Encrypting everything locally sounds great until someone needs to search for an old receipt.
Downloading the entire database to the phone for every single search burns mobile data and drains the battery.
We can instead send encrypted search tokens so the cloud looks up files without learning what we typed.
Even so, basic search leaks how many files matched each query.
Because every result size looks the same, the server cannot tell common words apart from rare ones.
Our system rounds candidate list lengths up to powers of two so the server only sees uniform response buckets.
The server only ever sees bucket sizes of four, eight, sixteen, or thirty-two items.
On Android, runtime garbage collection lets discarded keys sit in phone RAM for minutes.
We zero out the key buffer in RAM right after the encryption function returns.
Running lookups over ten thousand entries took 0.23 milliseconds on our K80 test phone and 1.48 milliseconds on the A14.
"""

evaluate_section(clean_intro_v9, "CLEAN INTRO V9")
