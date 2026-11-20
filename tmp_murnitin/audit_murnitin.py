import sys, os, json, re
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pypdf import PdfReader
from transformers import pipeline

INVISIBLE = {'\u200b':'Zero-Width Space','\u200c':'ZWNJ','\u200d':'ZWJ','\ufeff':'BOM','\u00ad':'Soft Hyphen'}

def detect_evasions(text):
    hidden = [{'character': name, 'occurrences': text.count(char)}
              for char, name in INVISIBLE.items() if text.count(char) > 0]
    homo = []
    for word in re.findall(r'\b\w+\b', text):
        latin = sum(1 for c in word if 65 <= ord(c) <= 90 or 97 <= ord(c) <= 122)
        cyril = sum(1 for c in word if 1024 <= ord(c) <= 1279)
        greek = sum(1 for c in word if 913 <= ord(c) <= 987)
        if latin > 0 and (cyril > 0 or greek > 0):
            homo.append({'word': word, 'Latin': latin, 'Cyrillic': cyril, 'Greek': greek})
    return hidden, homo

def clean_pdf_text(text):
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

print("Loading 3 Hugging Face Transformer models for Murnitin Neural Engine...")
pipe_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512)
pipe_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512)
pipe_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512)
print("All 3 models loaded successfully!")

pdf_path = sys.argv[1] if len(sys.argv) > 1 else "writing_paper/paper_ieee.pdf"
reader = PdfReader(pdf_path)
raw_text = " ".join(p.extract_text() or "" for p in reader.pages)

hidden, homo = detect_evasions(raw_text)
clean = raw_text
for ch in INVISIBLE:
    clean = clean.replace(ch, "")
clean = clean_pdf_text(clean)

raw_sents = re.split(r'(?<=[.!?])\s+', clean)
sentences = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]

print(f"\nAuditing {len(sentences)} sentences from {pdf_path}...")

# Run batch inference
preds_ahmed = pipe_ahmed(sentences, batch_size=16)
preds_fakespot = pipe_fakespot(sentences, batch_size=16)
preds_openai = pipe_openai(sentences, batch_size=16)

ai_direct = 0
ai_polished = 0
results = []

for i, (s, pa, pf, po) in enumerate(zip(sentences, preds_ahmed, preds_fakespot, preds_openai)):
    # ahmediqbal: label 'AI' = AI-generated
    score_ahmed = pa['score'] if pa['label'] == 'AI' else (1.0 - pa['score'])
    # fakespot: label 'AI' = AI-generated
    score_fakespot = pf['score'] if pf['label'] == 'AI' else (1.0 - pf['score'])
    # openai-detector: label 'Fake' = AI-generated, 'Real' = human
    score_openai = po['score'] if po['label'] == 'Fake' else (1.0 - po['score'])
    
    # Combined weighted score (50% ahmediqbal + 35% fakespot + 15% openai)
    combined = score_ahmed * 0.50 + score_fakespot * 0.35 + score_openai * 0.15
    
    cls = 'human'
    if combined > 0.60:
        cls = 'ai_direct'
        ai_direct += 1
    elif combined > 0.30:
        cls = 'ai_polished'
        ai_polished += 1
        
    results.append({
        'idx': i + 1,
        'text': s,
        'ahmed': round(score_ahmed, 3),
        'fakespot': round(score_fakespot, 3),
        'openai': round(score_openai, 3),
        'combined': round(combined, 3),
        'cls': cls
    })

# Score calculation from murnitin_server.py
total_sentences = len(sentences)
calibrated_score = ((ai_direct * 1.0 + ai_polished * 0.5) / total_sentences) * 100
if len(hidden) > 0 or len(homo) > 0:
    calibrated_score = max(calibrated_score, 85.0)

score = round(max(0.0, min(100.0, calibrated_score)))

if score < 25: verdict = "Likely Human"
elif score < 55: verdict = "Inconclusive / Mixed"
elif score < 80: verdict = "Likely AI-Assisted"
else: verdict = "Likely AI-Generated"
if len(hidden) > 0 or len(homo) > 0: verdict = "Evasion Detected"

print("\n" + "=" * 75)
print(f"MURNITIN PRODUCTION NEURAL ENSEMBLE REPORT: {pdf_path}")
print("=" * 75)
print(f"  AI Likelihood Score  : {score}%")
print(f"  Verdict              : {verdict}")
print(f"  Total Sentences      : {total_sentences}")
print(f"  AI-Direct Sentences  : {ai_direct} ({round(ai_direct/total_sentences*100, 1)}%)")
print(f"  AI-Polished Sentences: {ai_polished} ({round(ai_polished/total_sentences*100, 1)}%)")
print(f"  Human Sentences      : {total_sentences - ai_direct - ai_polished} ({round((total_sentences - ai_direct - ai_polished)/total_sentences*100, 1)}%)")
print(f"  Hidden Characters    : {len(hidden)}")
print(f"  Homoglyphs           : {len(homo)}")
print("=" * 75)

flagged = [r for r in results if r['cls'] != 'human']
print(f"\nFlagged Sentences ({len(flagged)} total):")
for r in sorted(flagged, key=lambda x: x['combined'], reverse=True):
    print(f"  [{r['idx']:03d}] {r['cls'].upper():11s} (comb={r['combined']:.2f} | ahmed={r['ahmed']:.2f}, fakespot={r['fakespot']:.2f}, openai={r['openai']:.2f})")
    print(f"        \"{r['text']}\"\n")
