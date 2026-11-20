import os, subprocess
import fitz

os.chdir(r"e:\_PROJECTS\visiocrypto\writing_paper")

eq_leakage = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb}
\begin{document}
\begin{align*}
\mathcal{L}_{\text{setup}}(\mathbf{D}) &= \left( n, \{|C_i|\}_{i=1}^n, \{\text{Pad}(|L_w|)\}_{w \in \mathbf{W}} \right) \\
\mathcal{L}_{\text{search}}(w) &= \left( \text{sp}(w), \text{Pad}(|L_w|) \right) \\
\mathcal{L}_{\text{update}}(op, D_j) &= \left( op, |D_j|, |\mathbf{W}_j| \right)
\end{align*}
\end{document}
"""

eq_hkdf = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb}
\begin{document}
\begin{align*}
K_{\text{enc}} &\leftarrow \text{HKDF-Expand}(K, \text{``VisioCrypt-Doc''}, 32) \\
K_{\text{search}} &\leftarrow \text{HKDF-Expand}(K, \text{``VisioCrypt-Search''}, 32) \\
K_{\text{index}} &\leftarrow \text{HKDF-Expand}(K, \text{``VisioCrypt-Payload''}, 32) \\
K_{\text{update}} &\leftarrow \text{HKDF-Expand}(K, \text{``VisioCrypt-Delta''}, 32)
\end{align*}
\end{document}
"""

eq_padding = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb}
\begin{document}
\begin{equation*}
|\text{Pad}(L_w)| = \max\left(4, 2^{\lceil \log_2 (|L_w|) \rceil}\right)
\end{equation*}
\end{document}
"""

eq_bloom = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb}
\begin{document}
\begin{equation*}
m = -\frac{n \ln p}{(\ln 2)^2} \approx 117 \text{ KB}, \quad k = \frac{m}{n} \ln 2 \approx 13
\end{equation*}
\end{document}
"""

eq_proof = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb}
\begin{document}
\begin{equation*}
\mathbf{Adv}_{\mathcal{A}}^{\text{IND-CKA2}}(k) \le \mathbf{Adv}_{\text{HMAC}}^{\text{PRF}}(\mathcal{B}_1) + \sum_{i=1}^n \mathbf{Adv}_{\text{CTR}}^{\text{CPA}}(\mathcal{B}_{2,i}) + \mathbf{Adv}_{\text{GCM}}^{\text{CPA}}(\mathcal{B}_3) + P_e
\end{equation*}
\end{document}
"""

math_blocks = {
    "eq_leakage": eq_leakage,
    "eq_hkdf": eq_hkdf,
    "eq_padding": eq_padding,
    "eq_bloom": eq_bloom,
    "eq_proof": eq_proof
}

for name, src in math_blocks.items():
    tex_file = f"figures/{name}.tex"
    pdf_file = f"figures/{name}.pdf"
    png_file = f"figures/{name}.png"
    with open(tex_file, "w", encoding="utf-8") as f:
        f.write(src)
    cmd = f"pdflatex -interaction=nonstopmode -output-directory=figures {tex_file}"
    subprocess.run(cmd, shell=True, check=True)
    doc = fitz.open(pdf_file)
    page = doc.load_page(0)
    mat = fitz.Matrix(600 / 72, 600 / 72)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    pix.save(png_file)
    doc.close()
    print(f"Generated 600 DPI {png_file} successfully!")
