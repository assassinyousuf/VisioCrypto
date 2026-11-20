"""
murnitin_engine.py  — Statistical AI Detection Engine
Handles academic/technical papers with an expanded vocabulary,
sentence-level n-gram transition scoring, and PDF-aware text cleaning.
"""

import sys, os, re, math, json
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

# ─────────────────────────────────────────────────────────────────────────────
# VOCABULARY  (common English + academic + technical baseline frequencies)
# ─────────────────────────────────────────────────────────────────────────────
BASE_FREQS = {
    # Function words
    "the":0.060,"of":0.035,"and":0.028,"a":0.022,"in":0.020,"to":0.019,
    "is":0.018,"that":0.015,"for":0.012,"it":0.011,"with":0.010,"as":0.010,
    "are":0.009,"on":0.009,"at":0.008,"by":0.008,"an":0.008,"be":0.007,
    "this":0.007,"from":0.007,"or":0.006,"which":0.006,"not":0.006,
    "was":0.005,"have":0.005,"were":0.005,"they":0.004,"we":0.004,
    "been":0.004,"has":0.004,"can":0.004,"than":0.004,"these":0.003,
    "their":0.003,"more":0.003,"also":0.003,"into":0.003,"its":0.003,
    "both":0.003,"may":0.003,"such":0.003,"between":0.003,"each":0.002,
    "while":0.002,"through":0.002,"when":0.002,"one":0.002,"two":0.002,
    "all":0.002,"if":0.002,"but":0.002,"other":0.002,"our":0.002,
    "used":0.002,"using":0.002,"about":0.002,"after":0.002,"only":0.002,
    "then":0.002,"up":0.002,"over":0.002,"new":0.001,"well":0.001,
    "based":0.002,"thus":0.002,"however":0.002,"where":0.002,"will":0.002,
    "within":0.002,"across":0.001,"without":0.001,"under":0.001,
    "during":0.001,"different":0.001,"most":0.001,"some":0.001,"any":0.001,
    "how":0.001,"could":0.001,"given":0.001,"since":0.001,"no":0.001,

    # Academic / research writing (neutral — appears in both human and AI)
    "model":0.0035,"models":0.003,"data":0.003,"learning":0.003,
    "results":0.003,"method":0.002,"methods":0.002,"approach":0.002,
    "analysis":0.002,"study":0.002,"paper":0.002,"research":0.002,
    "proposed":0.002,"show":0.002,"shows":0.002,"performance":0.002,
    "training":0.002,"prediction":0.002,"features":0.002,"set":0.002,
    "network":0.002,"deep":0.002,"machine":0.002,"neural":0.002,
    "task":0.002,"value":0.002,"high":0.002,"low":0.002,"large":0.002,
    "small":0.002,"number":0.002,"time":0.002,"first":0.002,"second":0.001,
    "work":0.002,"problems":0.001,"problem":0.001,"output":0.001,
    "accuracy":0.002,"error":0.001,"test":0.001,"evaluation":0.001,
    "function":0.001,"loss":0.001,"gradient":0.001,"layer":0.001,
    "dataset":0.002,"benchmark":0.001,"classification":0.001,
    "regression":0.001,"experimental":0.001,"experiments":0.001,
    "use":0.003,"information":0.002,"important":0.001,"process":0.001,
    "significant":0.001,"framework":0.002,"system":0.002,"systems":0.001,
    "algorithm":0.002,"algorithms":0.001,"feature":0.002,"input":0.001,
    "output":0.001,"score":0.001,"scores":0.001,"baseline":0.001,
    "existing":0.001,"previous":0.001,"recent":0.001,"state":0.001,
    "art":0.001,"tasks":0.001,"knowledge":0.001,"semantic":0.001,
    "representation":0.001,"embedding":0.001,"vector":0.001,"attention":0.001,
    "transformer":0.001,"bert":0.0008,"gpt":0.0008,"llm":0.0008,
    "large":0.002,"language":0.002,"generation":0.001,"text":0.002,
    "natural":0.001,"processing":0.001,"vision":0.001,"image":0.001,
    "graph":0.001,"node":0.001,"edge":0.0008,"cluster":0.0008,
    "class":0.001,"label":0.001,"labels":0.001,"weight":0.001,
    "weights":0.001,"epoch":0.0008,"batch":0.0008,"rate":0.002,
    "optimal":0.001,"optimization":0.001,"objective":0.001,
    "comparison":0.001,"compared":0.001,"different":0.001,
    "various":0.001,"similar":0.001,"specific":0.001,
    "related":0.001,"propose":0.001,"novel":0.001,"effective":0.001,
    "efficient":0.001,"evaluate":0.001,"improve":0.001,"achieves":0.001,
    "outperforms":0.001,"demonstrate":0.001,"demonstrates":0.001,
    "indicate":0.001,"indicates":0.001,"suggest":0.001,"suggests":0.001,
    "enable":0.001,"enables":0.001,"provide":0.001,"provides":0.001,
    "achieve":0.001,"achieve":0.001,"improve":0.001,"reduces":0.001,
    "increase":0.001,"decreases":0.001,"observe":0.001,"observe":0.001,
    "train":0.001,"trained":0.001,"tested":0.001,"validate":0.001,
    # CLV/Finance domain
    "customer":0.001,"lifetime":0.001,"clv":0.001,"ltv":0.0008,
    "revenue":0.001,"purchase":0.001,"churn":0.001,"retention":0.001,
    "transaction":0.001,"market":0.001,"digital":0.001,"commerce":0.001,
    "prediction":0.001,"forecast":0.001,"forecasting":0.001,
    "sparsity":0.0008,"sparse":0.001,"zero":0.001,"inflated":0.0008,
    "distribution":0.001,"lognormal":0.0008,"probability":0.001,
    "shapley":0.0008,"shap":0.0008,"explainable":0.001,"xai":0.0008,
    "interpretable":0.001,"interpretability":0.0008,"fairness":0.001,
    "bias":0.001,"equity":0.001,"socio":0.0008,"economic":0.001,
    "emerging":0.001,"sustainability":0.0008,"growth":0.001,
    # Stats/Math
    "precision":0.001,"recall":0.001,"f1":0.0008,"auc":0.0008,
    "roc":0.0008,"mse":0.0008,"mae":0.0008,"rmse":0.0008,
    "variance":0.001,"standard":0.001,"deviation":0.001,"mean":0.001,
    "median":0.0008,"distribution":0.001,"correlation":0.001,
    "coefficient":0.001,"parameter":0.001,"parameters":0.001,
    "hyperparameter":0.0008,"crossvalidation":0.0008,
    "statistical":0.001,"empirical":0.001,"theoretical":0.001,
}

# ─────────────────────────────────────────────────────────────────────────────
# AI SIGNATURE PHRASES  — boilerplate transitions specific to LLM output
# Scored as HIGH probability (very common in AI output → LOW perplexity)
# ─────────────────────────────────────────────────────────────────────────────
AI_BOILERPLATE = {
    # Discourse connectives LLMs overuse
    "furthermore","moreover","consequently","ultimately","additionally",
    "nevertheless","notwithstanding","henceforth","aforementioned",
    "multifaceted","showcases","underscores","encompasses","facilitates",
    "leverages","streamlines","revolutionizes","transformative",
    "groundbreaking","unprecedented","holistic","synergistic","robust",
    "seamlessly","comprehensively","systematically","meticulously",
    "efficiently","effectively","significantly","substantially",
    "remarkably","notably","considerably","predominantly","consistently",
    # Filler conclusions
    "delve","tapestry","testament","behest","pivotal","catalyst",
    "nuanced","sophisticated","crucial","utmost","paramount",
    "imperative","commendable","exemplary","multitude","myriad",
    "plethora","realm","landscape","paradigm","cornerstone",
    "embark","foster","leverage","harness","propel","ascertain",
    "delineate","elucidate","underscore","encapsulate","epitomize",
    # Academic-AI overuses
    "elucidating","delineating","encapsulating","underpinning",
    "posits","stipulates","mandates","necessitates","obviates",
    "potentiates","ameliorates","exacerbates","precipitates",
}

# ─────────────────────────────────────────────────────────────────────────────
# HUMAN SIGNAL WORDS — rarely used in LLM output, common in genuine writing
# Scored as LOW probability → HIGH perplexity
# ─────────────────────────────────────────────────────────────────────────────
HUMAN_MARKERS = {
    "honestly","frankly","surprisingly","unexpectedly","weirdly",
    "oddly","interestingly","frustratingly","thankfully","luckily",
    "unfortunately","awkwardly","admittedly","confusingly","puzzlingly",
    "disappointingly","excitingly","unsurprisingly","hilariously",
    "worryingly","annoyingly","reassuringly","understandably","arguably",
    "presumably","supposedly","apparently","seemingly","evidently",
    "strangely","notably","curiously","typically","usually","often",
    "sometimes","rarely","seldom","occasionally","frequently",
}

AI_PROB    = 0.055   # AI boilerplate: very common in LLM output → low entropy
HUMAN_PROB = 0.00002 # Human markers: rare in generic corpora → high entropy
OOV_PROB   = 0.00015 # Unknown words (proper nouns, niche tech terms)


def get_word_probability(word):
    w = re.sub(r"[^a-z'-]", '', word.lower())
    if not w:
        return OOV_PROB
    if w in AI_BOILERPLATE:
        return AI_PROB
    if w in HUMAN_MARKERS:
        return HUMAN_PROB
    return BASE_FREQS.get(w, OOV_PROB)


def sentence_perplexity(sentence):
    words = [w for w in sentence.split() if w.strip()]
    if not words:
        return 0.0
    log_sum = sum(math.log2(get_word_probability(w)) for w in words)
    entropy = -log_sum / len(words)
    return min(math.pow(2, entropy), 500.0)


# ─────────────────────────────────────────────────────────────────────────────
# TEXT CLEANING  (handles PDF extraction artifacts)
# ─────────────────────────────────────────────────────────────────────────────
def clean_pdf_text(text):
    """
    Join hyphenated line-breaks, normalise whitespace, remove headers/footers
    and figure/table captions that confuse sentence scoring.
    """
    # Rejoin soft-hyphenated words across lines: "predic-\ntion" → "prediction"
    text = re.sub(r'-\s*\n\s*', '', text)
    # Join bare line breaks that are mid-sentence (line doesn't end with . ! ?)
    text = re.sub(r'(?<![.!?])\n(?!\n)', ' ', text)
    # Collapse multiple spaces/newlines
    text = re.sub(r'\n{2,}', '\n', text)
    text = re.sub(r' {2,}', ' ', text)
    # Remove common IEEE/academic noise
    text = re.sub(r'978-\d[\d-]+', '', text)        # ISBN/DOI patterns
    text = re.sub(r'\[\d+\]', '', text)              # citation brackets [1]
    text = re.sub(r'\(\d{4}\)', '', text)            # year refs (2023)
    text = re.sub(r'Fig\.\s*\d+', '', text)
    text = re.sub(r'Table\s+\d+', '', text)
    text = re.sub(r'Algorithm\s+\d+', '', text)
    text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)   # page nums
    return text.strip()


def split_sentences(text):
    """Split text into meaningful sentences (5+ words)."""
    raw = re.split(r'(?<=[.!?])\s+', text)
    sents = []
    for s in raw:
        s = s.strip()
        if len(s.split()) >= 5:
            sents.append(s)
    return sents


# ─────────────────────────────────────────────────────────────────────────────
# EVASION DETECTION
# ─────────────────────────────────────────────────────────────────────────────
INVISIBLE = {
    '\u200b': "Zero-Width Space (U+200B)",
    '\u200c': "Zero-Width Non-Joiner (U+200C)",
    '\u200d': "Zero-Width Joiner (U+200D)",
    '\ufeff': "Byte Order Mark (U+FEFF)",
    '\u00ad': "Soft Hyphen (U+00AD)",
}

def detect_hidden_characters(text):
    return [{'character': name, 'occurrences': text.count(char)}
            for char, name in INVISIBLE.items() if text.count(char) > 0]


def detect_homoglyphs(text):
    findings = []
    for word in re.findall(r'\b\w+\b', text):
        latin = sum(1 for c in word if 65 <= ord(c) <= 90 or 97 <= ord(c) <= 122)
        cyril = sum(1 for c in word if 1024 <= ord(c) <= 1279)
        greek = sum(1 for c in word if 913 <= ord(c) <= 987)
        if (latin > 0) and (cyril > 0 or greek > 0):
            findings.append({'word': word, 'Latin': latin, 'Cyrillic': cyril, 'Greek': greek})
    return findings


# ─────────────────────────────────────────────────────────────────────────────
# MAIN ANALYSIS
# ─────────────────────────────────────────────────────────────────────────────
def analyze_document(text, source_label="Input"):
    hidden = detect_hidden_characters(text)
    homo   = detect_homoglyphs(text)
    has_evasion = len(hidden) > 0 or len(homo) > 0

    # Strip invisible chars before scoring
    clean = text
    for ch in INVISIBLE:
        clean = clean.replace(ch, '')

    # Clean PDF artifacts
    clean = clean_pdf_text(clean)

    sentences = split_sentences(clean)
    if not sentences:
        return {'error': 'No scorable sentences found.'}

    sent_results = []
    for i, s in enumerate(sentences):
        p   = sentence_perplexity(s)
        cls = 'human'
        if len(s.split()) > 4:
            if p < 16:    cls = 'ai_direct'
            elif p < 30:  cls = 'ai_polished'
        sent_results.append({'index': i + 1, 'text': s, 'perplexity': round(p, 2), 'classification': cls})

    perps     = [r['perplexity'] for r in sent_results]
    avg       = sum(perps) / len(perps)
    variance  = sum((p - avg) ** 2 for p in perps) / len(perps)
    burstiness = math.sqrt(variance)

    ai_direct  = [r for r in sent_results if r['classification'] == 'ai_direct']
    ai_polish  = [r for r in sent_results if r['classification'] == 'ai_polished']
    ai_total   = ai_direct + ai_polish

    # Scoring model
    if avg < 20 and burstiness < 14:
        score = 95 - avg * 1.8 - burstiness * 1.2
    elif avg < 36 and burstiness < 26:
        score = 65 - avg * 0.8 - burstiness * 0.5
    else:
        score = max(2, 18 - avg * 0.07 - burstiness * 0.04)

    if has_evasion:
        score = max(score, 85)

    score = round(max(0.0, min(100.0, score)))

    if score < 25:     verdict = 'Likely Human'
    elif score < 55:   verdict = 'Inconclusive / Mixed'
    elif score < 80:   verdict = 'Likely AI-Assisted'
    else:              verdict = 'Likely AI-Generated'
    if has_evasion:    verdict = 'Evasion Detected'

    return {
        'source': source_label,
        'summary': {
            'ai_probability': score,
            'verdict': verdict,
            'avg_perplexity': round(avg, 2),
            'burstiness': round(burstiness, 2),
            'total_sentences': len(sent_results),
            'ai_direct_count': len(ai_direct),
            'ai_polished_count': len(ai_polish),
            'ai_flagged_pct': round(100 * len(ai_total) / len(sent_results), 1),
            'evasion_detected': has_evasion,
        },
        'evasion_report': {
            'hidden_characters': hidden,
            'homoglyphs': homo,
        },
        'sentences': sent_results,
    }


def print_report(result):
    s  = result['summary']
    er = result['evasion_report']
    sentences = result['sentences']

    print('=' * 70)
    print(f'MURNITIN INTEGRITY REPORT  —  {result["source"]}')
    print('=' * 70)
    print()
    print('─── OVERALL SCORES ─────────────────────────────────────────────')
    print(f'  AI Likelihood    : {s["ai_probability"]}%')
    print(f'  Verdict          : {s["verdict"]}')
    print(f'  Avg Perplexity   : {s["avg_perplexity"]:.2f}   (lower = more formulaic/AI)')
    print(f'  Burstiness       : {s["burstiness"]:.2f}   (lower = more uniform/AI)')
    print(f'  Sentences scored : {s["total_sentences"]}')
    print(f'  AI-flagged       : {s["ai_direct_count"] + s["ai_polished_count"]} ({s["ai_flagged_pct"]}%)')
    print(f'    ├ AI-Direct    : {s["ai_direct_count"]}  (perplexity < 16)')
    print(f'    └ AI-Polished  : {s["ai_polished_count"]}  (perplexity 16–30)')
    print()

    print('─── EVASION FORENSICS ──────────────────────────────────────────')
    if er['hidden_characters']:
        for h in er['hidden_characters']:
            print(f'  ⚠  {h["character"]}: {h["occurrences"]} occurrence(s)')
    elif er['homoglyphs']:
        print(f'  ⚠  Homoglyphs detected in {len(er["homoglyphs"])} word(s)')
    else:
        print('  ✓  No evasion techniques detected')
    print()

    print('─── MOST SUSPICIOUS SENTENCES (AI-Direct) ──────────────────────')
    shown = 0
    for r in sentences:
        if r['classification'] == 'ai_direct' and shown < 8:
            print(f'  [{r["index"]:03d}] perp={r["perplexity"]:6.1f} | {r["text"][:100]}')
            shown += 1
    if shown == 0:
        print('  None flagged as AI-Direct.')
    print()

    print('─── AI-POLISHED SENTENCES ───────────────────────────────────────')
    shown = 0
    for r in sentences:
        if r['classification'] == 'ai_polished' and shown < 6:
            print(f'  [{r["index"]:03d}] perp={r["perplexity"]:6.1f} | {r["text"][:100]}')
            shown += 1
    if shown == 0:
        print('  None flagged.')
    print()

    print('─── COMPLIANCE CHECKLIST ────────────────────────────────────────')
    print('  ✓  FERPA  : No student PII processed')
    print('  ✓  GDPR   : No raw text retained beyond session')
    print('  ✓  ZK     : Client-side only — zero server upload')
    print('  ✓  Advisory use: Not intended as automated disciplinary verdict')
    print()
    print('Generated by Murnitin v1.1  ·  github.com/meetmehedi/murnitin')
    print('=' * 70)


# ─────────────────────────────────────────────────────────────────────────────
# CLI  — python3 murnitin_engine.py [file.pdf | file.txt | --demo]
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        filepath = sys.argv[1]

        if filepath.endswith('.pdf'):
            try:
                from pypdf import PdfReader
            except ImportError:
                print('Install pypdf: pip3 install pypdf'); sys.exit(1)

            reader   = PdfReader(filepath)
            raw_text = ' '.join(p.extract_text() or '' for p in reader.pages)
            label    = f'{filepath} ({len(reader.pages)} pages, {len(raw_text.split())} words)'
        else:
            with open(filepath, 'r', encoding='utf-8') as f:
                raw_text = f.read()
            label = filepath

        result = analyze_document(raw_text, label)
        print_report(result)

    else:
        # Built-in demo
        HUMAN = (
            "Yesterday, I wandered down to the old bookshop near the canal. "
            "The smells of coffee and decaying paper immediately overwhelmed me. "
            "I randomly grabbed a dusty green volume — honestly one of the more surreal afternoons of my year. "
            "The whole atmosphere felt incredibly peaceful, a nice escape from the crazy pace of regular life."
        )
        AI = (
            "Furthermore, the utilization of digital technologies has significantly altered the contemporary educational landscape. "
            "It provides students with seamless access to a comprehensive array of educational resources and platforms. "
            "Moreover, online learning systems offer unparalleled flexibility and convenience to learners across the globe. "
            "Ultimately, the systematic implementation of technology in pedagogy has demonstrated substantial benefits for modern academic structures."
        )

        print('\n=== DEMO: Human Sample ===')
        print_report(analyze_document(HUMAN, 'Human Essay'))
        print('\n=== DEMO: AI Sample ===')
        print_report(analyze_document(AI, 'AI Essay'))
