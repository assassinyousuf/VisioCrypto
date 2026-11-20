import sys, re

text = """Multi-Device Search Query Latency.
Looking up words took 0.23 ms on the K80 and 1.48 ms on the Galaxy A14 for 10,000 keywords."""

def clean_pdf_text(text):
    text = re.sub(r'-\s*\n\s*', '', text)
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

clean = clean_pdf_text(text)
raw_sents = re.split(r'(?<=[.!?])\s+', clean)
sentences = [s.strip() for s in raw_sents if len(s.strip().split()) >= 4]

print("Extracted sentences:")
for s in sentences:
    print(f"-> \"{s}\"")
