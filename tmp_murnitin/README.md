# Murnitin

**Murnitin** is a next-generation, privacy-first academic integrity platform designed to be more transparent, equitable, and secure than Turnitin. 

Rather than acting as a punitive black box, Murnitin leverages **Explainable AI (XAI)**, **Linguistic Feature Inspection**, and **Writing Process Verification** to provide instructors with evidence-based signals instead of arbitrary scores.

---

## 🚀 Key Differentiators (Why Murnitin Beats Turnitin)

### 1. Explainable AI (XAI) Dashboard
Turnitin surfaces a single, opaque percentage score (e.g., "78% AI-Generated") that teachers often treat as a final verdict. Murnitin maps sentence-level probabilities and highlights exact patterns, showing:
* **Perplexity anomalies** (how "predictable" the text is).
* **Burstiness variance** (the natural rhythm and length changes of sentences).
* **Repetitive n-grams** and formulaic syntax structures.

### 2. Typographical & Adversarial Defense
Murnitin automatically flags common evasion strategies that bypass typical detectors:
* **Homoglyphs**: Mixed Cyrillic/Greek characters designed to confuse word boundaries.
* **Hidden Characters**: Invisible Unicode characters or zero-width spaces inserted between letters.
* **Synonym Swaps**: Repetitive use of AI paraphraser synonyms.

### 3. Writing Process Verification (Draft Timeline)
Instead of judging the final static document, Murnitin allows students to attach their Google Docs or MS Word draft timelines. 
* Murnitin analyzes the typing dynamics (active writing hours, editing spurts, large block copy-pastes) to verify a natural, human drafting timeline.
* AI-generated copy-pastes are flagged immediately, while slow, iterative human typing is validated even if the style resembles formal language patterns.

### 4. GDPR & Zero-Knowledge Institutional Database
Turnitin forces institutions to upload and index all student papers in a proprietary global database, creating severe privacy and copyright issues under GDPR/FERPA.
* Murnitin offers **Zero-Knowledge Indexing**: Submissions are converted to irreversible cryptographic shingles/hashes. Murnitin can detect similarities without ever storing or reconstructing the original text.
* Institutional boundaries are fully respected. Schools can choose **Local-Only Scans** or ephemeral checks.

---

## 🛠 Tech Stack

* **Backend Engine**: Python (scikit-learn, transformers, numpy)
* **Frontend Dashboard**: Vanilla HTML5, CSS3 (Glassmorphism, custom dark mode, transition effects), and vanilla JavaScript.

---

## 💻 Running the Prototype Dashboard

To view the Murnitin visual dashboard, open [index.html](file:///Users/md.mehedihasan/murnitin/index.html) directly in any modern browser. 
To run a test with the statistical backend, use the Python engine:
```bash
python3 murnitin_engine.py
```
