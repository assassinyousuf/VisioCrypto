import pypdf, re

def clean_pdf_text(text):
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

reader = pypdf.PdfReader("writing_paper/paper_ieee.pdf")
full_text = ""
for page in reader.pages:
    txt = page.extract_text()
    if txt:
        full_text += txt + "\n"

clean_text = clean_pdf_text(full_text)
raw_sents = re.split(r'(?<=[.!?])\s+', clean_text)
sents = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]

print(f"Total extracted sentences: {len(sents)}")
for i, s in enumerate(sents):
    print(f"[{i:03d}] {s}\n")
