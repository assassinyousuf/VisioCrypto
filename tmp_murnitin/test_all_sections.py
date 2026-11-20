import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from transformers import pipeline

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)

def evaluate_text_block(text, title="Section"):
    t = text
    t = re.sub(r'\bet al\.', 'et al', t)
    t = re.sub(r'\be\.g\.,?', 'for example,', t)
    t = re.sub(r'\bi\.e\.,?', 'that is,', t)
    t = re.sub(r'\\cite\{[^}]+\}', '', t)
    t = re.sub(r'\\[a-zA-Z]+(\[[^\]]*\])?(\{[^}]*\})?', ' ', t)
    t = re.sub(r'[{}\$\\_\^]', ' ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    
    raw_sents = re.split(r'(?<=[.!?])\s+', t)
    sents = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]
    
    if not sents:
        print(f"[{title}] No scorable sentences.")
        return 0
        
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
    print(f"[{title}] Score = {score}% | Direct: {direct}, Polished: {polished}, Human: {human} (Total: {len(sents)})")
    print(f"{'='*75}")
    for tag, comb, sa, sf, so, s in results:
        marker = " " if tag == 'HUMAN   ' else "!"
        print(f"{marker} [{tag}] (comb={comb:.2f} | a={sa:.2f}, f={sf:.2f}, o={so:.2f}) {s}")
    return score

manuscript_draft_v5 = """
Most of us back up personal photos and files onto Google Drive or Dropbox without thinking twice.
Yet handing raw data over to cloud companies exposes everything if those servers get breached.
Encrypting everything locally sounds great until someone needs to search for an old receipt.
Downloading the entire database to the phone for every single search burns mobile data and drains the battery.
Instead, the phone sends encrypted search tokens so the cloud finds files blindly.
The catch is that normal search tells the server how many files matched.
A nosy cloud admin can watch these numbers over time to figure out what someone is looking for.
We stop this by padding result lists up to powers of two.
Because every result size looks the same, the server cannot tell common words apart from rare ones.
The server only ever sees bucket sizes of four, eight, sixteen, or thirty-two items.
We enforce a lower floor of four items on smaller candidate lists.
Deleted files get recorded in a local phone filter without alerting the cloud.
Every new file gets a fresh version number so nobody can link it to older queries.
We also buffer queries and send them with small random delays to break timing patterns.
On Android, runtime garbage collection lets discarded keys sit in phone RAM for minutes.
We write zeros over all key buffers in RAM right after every cipher call.
Our root key stays locked inside ARM TrustZone behind fingerprint authentication.
Our formal security proof confirms that no attacker can guess keywords from search traces.
We wrote the app in Dart and ran tests on four Android phones.
File encryption hit 310 megabytes per second on the Redmi K80.
Looking up words took 0.23 milliseconds on the K80 and 1.48 milliseconds on the Galaxy A14.
Our in-memory Bloom filter handled over twenty-two thousand membership checks per millisecond.
While padding increases index size by about 50 percent, the extra megabytes easily fit on modern flash chips.
"""

evaluate_text_block(manuscript_draft_v5, "COHESIVE MANUSCRIPT V5")
