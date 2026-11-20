import re, sys
sys.stdout.reconfigure(encoding='utf-8')

with open("C:/Users/User/.gemini/antigravity-ide/brain/3ec76b47-f4f4-4509-8cbf-7679704cad2f/.system_generated/tasks/task-475.log", "r", encoding="utf-8") as f:
    content = f.read()

flagged_blocks = re.findall(r'\[(\d{3})\] (AI_DIRECT|AI_POLISHED)\s+\(comb=([\d\.]+).*?\)\s+"(.*?)"', content, re.DOTALL)

print(f"Total flagged in log: {len(flagged_blocks)}")
print("\n--- AI_DIRECT SENTENCES ---")
for num, kind, comb, text in flagged_blocks:
    if kind == "AI_DIRECT":
        cleaned_t = " ".join(text.split())
        print(f"[{num}] ({comb}) {cleaned_t}")

print("\n--- SAMPLE AI_POLISHED SENTENCES ---")
for num, kind, comb, text in flagged_blocks[:20]:
    if kind == "AI_POLISHED":
        cleaned_t = " ".join(text.split())
        print(f"[{num}] ({comb}) {cleaned_t}")
