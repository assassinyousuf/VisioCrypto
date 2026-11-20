import os, subprocess
import fitz

os.chdir(r"e:\_PROJECTS\visiocrypto\writing_paper")

bib_tex = r"""\documentclass[10pt,conference,letterpaper]{IEEEtran}
\usepackage{cite}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{balance}
\pagestyle{empty}
\thispagestyle{empty}
\begin{document}
\nocite{*}
\bibliographystyle{IEEEtran}
\bibliography{references}
\end{document}
"""

with open("figures/bib_standalone.tex", "w", encoding="utf-8") as f:
    f.write(bib_tex)

subprocess.run("pdflatex -interaction=nonstopmode -output-directory=figures figures/bib_standalone.tex", shell=True, check=True)
subprocess.run("bibtex figures/bib_standalone", shell=True, check=True)
subprocess.run("pdflatex -interaction=nonstopmode -output-directory=figures figures/bib_standalone.tex", shell=True, check=True)
subprocess.run("pdflatex -interaction=nonstopmode -output-directory=figures figures/bib_standalone.tex", shell=True, check=True)

# Render page 1 of bib_standalone.pdf to high-res PNG
doc = fitz.open("figures/bib_standalone.pdf")
page = doc.load_page(0)
# Extract only the references column rect
# Let's see: page size is 612 x 792 pt
rect = page.rect
mat = fitz.Matrix(600 / 72, 600 / 72)
pix = page.get_pixmap(matrix=mat, alpha=False)
pix.save("figures/bib_rendered.png")
doc.close()
print("Rendered 600 DPI figures/bib_rendered.png successfully!")
