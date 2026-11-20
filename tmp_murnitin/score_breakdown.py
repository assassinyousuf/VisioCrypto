import sys, json
sys.stdout.reconfigure(encoding='utf-8')

with open('tmp_murnitin/full_audit_results.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

sents = data['sentences']

ref_score, table_score, math_score, body_score = 0, 0, 0, 0
ref_count, table_count, math_count, body_count = 0, 0, 0, 0

print("=== DETAILED BREAKDOWN OF CURRENT AUDIT ===")

for s in sents:
    t = s['text']
    comb = s['comb']
    pts = 1.0 if comb > 0.60 else (0.5 if comb > 0.30 else 0.0)
    
    is_ref = any(kw in t for kw in ["Proc.", "IEEE", "ACM", "Trans.", "arXiv:", "pp.", "vol.", "no.", "Security, 20", "CCS, 20", "S&P, 20"])
    is_table = any(kw in t for kw in ["TABLE", "Tier 1", "MB/s", "Linear Scanning", "Redmi K80", "Helio G88", "LPDDR", "UFS", "eMMC"])
    is_math = any(kw in t for kw in ["Algorithm", "Require:", "Ensure:", "HKDF-SHA256", "AES-GCM", "Game", "AdvIND", "Ldyn-VH", "Definition 1", "Theorem 1", "AdvCPA", "Pr["])
    
    if is_ref:
        ref_count += 1
        ref_score += pts
        cat = "REF"
    elif is_table:
        table_count += 1
        table_score += pts
        cat = "TABLE"
    elif is_math:
        math_count += 1
        math_score += pts
        cat = "MATH"
    else:
        body_count += 1
        body_score += pts
        cat = "BODY"
        if pts > 0:
            print(f"[BODY FLAGGED] ({comb:.2f}) {t}")

print(f"\n--- Category Contributions to the 41% Score ---")
print(f"1. References ({ref_count} items): {ref_score} penalty points ({round(ref_score/len(sents)*100, 1)}% of total score)")
print(f"2. Tables & Figures ({table_count} items): {table_score} penalty points ({round(table_score/len(sents)*100, 1)}% of total score)")
print(f"3. Math & Algorithms ({math_count} items): {math_score} penalty points ({round(math_score/len(sents)*100, 1)}% of total score)")
print(f"4. Narrative Body Prose ({body_count} items): {body_score} penalty points ({round(body_score/len(sents)*100, 1)}% of total score)")
print(f"Total Penalty: {ref_score + table_score + math_score + body_score} / {len(sents)} = {round((ref_score + table_score + math_score + body_score)/len(sents)*100)}%")
