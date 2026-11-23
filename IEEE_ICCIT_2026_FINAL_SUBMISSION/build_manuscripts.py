import shutil
import re

# Read test_listing_fix.tex as baseline
with open('g:/_PROJECTS/visiocrypto/IEEE_ICCIT_2026_FINAL_SUBMISSION/test_listing_fix.tex', 'r', encoding='utf-8') as f:
    clean_tex = f.read()

# 1. Write 2015_Revised_Manuscript.tex
with open('g:/_PROJECTS/visiocrypto/IEEE_ICCIT_2026_FINAL_SUBMISSION/2015_Revised_Manuscript.tex', 'w', encoding='utf-8') as f:
    f.write(clean_tex)
print('Wrote 2015_Revised_Manuscript.tex')

# 2. Build 2015_Highlighted_Manuscript.tex
high_tex = clean_tex

# Insert color definition in preamble
preamble_highlight = '''\\definecolor{revcolor}{RGB}{0, 40, 160}
\\newenvironment{revised}{\\color{revcolor}}{}
\\newcommand{\\rev}[1]{\\textcolor{revcolor}{#1}}
'''
high_tex = high_tex.replace('\\begin{document}', preamble_highlight + '\n\\begin{document}')

# Add \\begin{revised} before Section II
high_tex = high_tex.replace('\\section{Related Work and Foundations}', '\\begin{revised}\n\\section{Related Work and Foundations}')

# Add \\end{revised} before Section IX (Conclusion)
high_tex = high_tex.replace('\\section{Conclusion}', '\\end{revised}\n\\section{Conclusion}')

with open('g:/_PROJECTS/visiocrypto/IEEE_ICCIT_2026_FINAL_SUBMISSION/2015_Highlighted_Manuscript.tex', 'w', encoding='utf-8') as f:
    f.write(high_tex)
print('Wrote 2015_Highlighted_Manuscript.tex')
