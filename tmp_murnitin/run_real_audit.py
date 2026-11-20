import sys, os, json, re, time
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from pypdf import PdfReader
import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
print(f"[Device] Using device: {'CUDA GPU (0)' if device == 0 else 'CPU'}", flush=True)

print("Loading 3 Hugging Face Transformer models for Murnitin Neural Engine...", flush=True)
t0 = time.time()
pipe_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
print(f"[OK] Model 1/3 (ahmediqbal) loaded in {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
pipe_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
print(f"[OK] Model 2/3 (fakespot) loaded in {time.time()-t0:.1f}s", flush=True)

t0 = time.time()
pipe_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)
print(f"[OK] Model 3/3 (openai-detector) loaded in {time.time()-t0:.1f}s", flush=True)

def clean_pdf_text(text):
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

pdf_path = sys.argv[1] if len(sys.argv) > 1 else "writing_paper/paper_ieee.pdf"
reader = PdfReader(pdf_path)
raw_text = " ".join(p.extract_text() or "" for p in reader.pages)
clean = clean_pdf_text(raw_text)

raw_sents = re.split(r'(?<=[.!?])\s+', clean)
sentences = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]

print(f"\nExtracted {len(sentences)} sentences from {pdf_path}. Running batch inference...", flush=True)

t0 = time.time()
preds_ahmed = pipe_ahmed(sentences, batch_size=32)
preds_fakespot = pipe_fakespot(sentences, batch_size=32)
preds_openai = pipe_openai(sentences, batch_size=32)
print(f"Batch inference completed in {time.time()-t0:.1f}s", flush=True)

ai_direct = 0
ai_polished = 0
results = []

for i, (s, pa, pf, po) in enumerate(zip(sentences, preds_ahmed, preds_fakespot, preds_openai)):
    score_ahmed = pa['score'] if pa['label'] == 'AI' else (1.0 - pa['score'])
    score_fakespot = pf['score'] if pf['label'] == 'AI' else (1.0 - pf['score'])
    score_openai = po['score'] if po['label'] == 'Fake' else (1.0 - po['score'])
    
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

total_sentences = len(sentences)
calibrated_score = ((ai_direct * 1.0 + ai_polished * 0.5) / total_sentences) * 100
score = round(max(0.0, min(100.0, calibrated_score)))

if score < 25: verdict = "Likely Human"
elif score < 55: verdict = "Inconclusive / Mixed"
elif score < 80: verdict = "Likely AI-Assisted"
else: verdict = "Likely AI-Generated"

print("\n" + "=" * 75, flush=True)
print(f"MURNITIN PRODUCTION NEURAL ENSEMBLE REPORT: {pdf_path}", flush=True)
print("=" * 75, flush=True)
print(f"  AI Likelihood Score  : {score}%", flush=True)
print(f"  Verdict              : {verdict}", flush=True)
print(f"  Total Sentences      : {total_sentences}", flush=True)
print(f"  AI-Direct Sentences  : {ai_direct} ({round(ai_direct/total_sentences*100, 1)}%)", flush=True)
print(f"  AI-Polished Sentences: {ai_polished} ({round(ai_polished/total_sentences*100, 1)}%)", flush=True)
print(f"  Human Sentences      : {total_sentences - ai_direct - ai_polished} ({round((total_sentences - ai_direct - ai_polished)/total_sentences*100, 1)}%)", flush=True)
print("=" * 75, flush=True)

flagged = [r for r in results if r['cls'] != 'human']
print(f"\nFlagged Sentences ({len(flagged)} total):", flush=True)
for r in sorted(flagged, key=lambda x: x['combined'], reverse=True):
    print(f"  [{r['idx']:03d}] {r['cls'].upper():11s} (comb={r['combined']:.2f} | ahmed={r['ahmed']:.2f}, fakespot={r['fakespot']:.2f}, openai={r['openai']:.2f})", flush=True)
    print(f"        \"{r['text']}\"\n", flush=True)
