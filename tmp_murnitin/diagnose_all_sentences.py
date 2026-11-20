import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

from pypdf import PdfReader
import torch
from transformers import pipeline

device = 0 if torch.cuda.is_available() else -1
print(f"Loading models on {'CUDA' if device == 0 else 'CPU'}...", flush=True)

p_ahmed = pipeline("text-classification", model="ahmediqbal/ai-text-detector-model", truncation=True, max_length=512, device=device)
p_fakespot = pipeline("text-classification", model="fakespot-ai/roberta-base-ai-text-detection-v1", truncation=True, max_length=512, device=device)
p_openai = pipeline("text-classification", model="roberta-base-openai-detector", truncation=True, max_length=512, device=device)

def clean_pdf_text(text):
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

pdf_path = "writing_paper/paper_ieee.pdf"
reader = PdfReader(pdf_path)
raw_text = " ".join(p.extract_text() or "" for p in reader.pages)
clean = clean_pdf_text(raw_text)

raw_sents = re.split(r'(?<=[.!?])\s+', clean)
sentences = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]

print(f"Scoring {len(sentences)} sentences...", flush=True)
preds_ahmed = p_ahmed(sentences, batch_size=32)
preds_fakespot = p_fakespot(sentences, batch_size=32)
preds_openai = p_openai(sentences, batch_size=32)

direct, polished, human = 0, 0, 0
results = []

for i, (s, pa, pf, po) in enumerate(zip(sentences, preds_ahmed, preds_fakespot, preds_openai)):
    score_ahmed = pa['score'] if pa['label'] == 'AI' else (1.0 - pa['score'])
    score_fakespot = pf['score'] if pf['label'] == 'AI' else (1.0 - pf['score'])
    score_openai = po['score'] if po['label'] == 'Fake' else (1.0 - po['score'])
    
    combined = score_ahmed * 0.50 + score_fakespot * 0.35 + score_openai * 0.15
    
    if combined > 0.60:
        cls = 'DIRECT'
        direct += 1
    elif combined > 0.30:
        cls = 'POLISHED'
        polished += 1
    else:
        cls = 'HUMAN'
        human += 1
        
    results.append({
        'idx': i + 1,
        'cls': cls,
        'comb': round(combined, 3),
        'ahmed': round(score_ahmed, 3),
        'fakespot': round(score_fakespot, 3),
        'openai': round(score_openai, 3),
        'text': s
    })

score = round(((direct * 1.0 + polished * 0.5) / len(sentences)) * 100)
print(f"\n=======================================================")
print(f"AUDIT SUMMARY: Score = {score}% | Direct: {direct}, Polished: {polished}, Human: {human} (Total: {len(sentences)})")
print(f"=======================================================")

with open("tmp_murnitin/full_audit_results.json", "w", encoding="utf-8") as f:
    json.dump({'score': score, 'direct': direct, 'polished': polished, 'human': human, 'total': len(sentences), 'sentences': results}, f, indent=2)

print("Saved full diagnostics to tmp_murnitin/full_audit_results.json", flush=True)
