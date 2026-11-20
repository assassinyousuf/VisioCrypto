import pypdf, re, json, sys
sys.stdout.reconfigure(encoding='utf-8')

def clean_pdf_text(text):
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

reader = pypdf.PdfReader("writing_paper/paper_ieee.pdf")
full_text = " ".join(p.extract_text() or "" for p in reader.pages)
clean = clean_pdf_text(full_text)
raw_sents = re.split(r'(?<=[.!?])\s+', clean)
sentences = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]

print(f"Total sentences extracted: {len(sentences)}")
for i, s in enumerate(sentences):
    # check if reference
    is_ref = any(kw in s for kw in ["Proc.", "IEEE", "ACM", "Trans.", "arXiv:", "pp."])
    is_table = any(kw in s for kw in ["TABLE", "Tier 1", "MB/s", "Linear Scanning", "Redmi K80"])
    is_alg = any(kw in s for kw in ["Algorithm", "Require:", "Ensure:", "HKDF-SHA256", "AES-GCM"])
    tag = "REF" if is_ref else ("TABLE" if is_table else ("ALG" if is_alg else "PROSE"))
    print(f"[{i+1:03d}] [{tag:5s}] {s[:80]}...")
