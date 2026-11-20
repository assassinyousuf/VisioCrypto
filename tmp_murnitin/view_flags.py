import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open('tmp_murnitin/full_audit_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sents = data['sentences']
human = [s for s in sents if s['cls'] == 'HUMAN']
polished = [s for s in sents if s['cls'] == 'POLISHED']
direct = [s for s in sents if s['cls'] == 'DIRECT']

print(f"Total: {len(sents)}, Human: {len(human)}, Polished: {len(polished)}, Direct: {len(direct)}")

print("\n=== DIRECT SENTENCES (Score > 0.60) ===")
for s in direct:
    print(f"[{s['idx']:03d}] (comb={s['comb']:.2f} | a={s['ahmed']:.2f}, f={s['fakespot']:.2f}, o={s['openai']:.2f})")
    print(f"      {s['text']}\n")

print("\n=== POLISHED SENTENCES (Score 0.30 - 0.60) (First 30) ===")
for s in polished[:30]:
    print(f"[{s['idx']:03d}] (comb={s['comb']:.2f} | a={s['ahmed']:.2f}, f={s['fakespot']:.2f}, o={s['openai']:.2f})")
    print(f"      {s['text']}\n")
