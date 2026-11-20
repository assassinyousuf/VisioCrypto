import os, subprocess
import fitz

os.chdir(r"e:\_PROJECTS\visiocrypto\writing_paper")

alg_tex = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb,algorithmicx,algpseudocode}
\begin{document}
\noindent\textbf{Algorithm 1: VisioCrypt Encrypted Index Generation}
\vspace{1mm}\hrule\vspace{1mm}
\begin{algorithmic}[1]
\Require Plaintext collection $\mathbf{D} = \{D_1, \dots, D_n\}$, master key $K$
\Ensure Encrypted multi-map $\mathbf{I}$, ciphertexts $\mathbf{C}$
\State $(K_{\text{enc}}, K_{\text{search}}, K_{\text{index}}, K_{\text{update}}) \leftarrow \text{HKDF-Expand}(K)$
\State $\mathbf{W} \leftarrow \text{ExtractKeywords}(\mathbf{D})$, $\mathbf{I} \leftarrow \text{EmptyMap}()$
\For{each distinct keyword $w \in \mathbf{W}$}
    \State $L_w \leftarrow \text{GetMatchingDocs}(\mathbf{D}, w)$, $t \leftarrow |\text{Pad}(L_w)|$
    \State $L_w^* \leftarrow L_w \parallel \text{Repeat}(\text{DUMMY}, t - |L_w|)$
    \State $T_w \leftarrow \text{HMAC}(K_{\text{search}}, w \parallel 1)$
    \State $iv \leftarrow \text{SecureRandom}(12)$
    \State $E_w \leftarrow \text{AES-GCM-Enc}(K_{\text{index}}, iv, L_w^*)$
    \State $\mathbf{I}[T_w] \leftarrow (iv \parallel E_w)$
\EndFor
\For{each document $D_i \in \mathbf{D}$}
    \State $C_i \leftarrow \text{AES-CTR-Enc}(K_{\text{enc}}, D_i) \parallel \text{HMAC}(K_{\text{enc}}, C_i)$
    \State $\mathbf{C} \leftarrow \mathbf{C} \cup \{C_i\}$
\EndFor
\State \textbf{ZeroizeMemory}($\{K_{\text{enc}}, K_{\text{search}}, K_{\text{index}}, K_{\text{update}}\}$)
\State \Return $(\mathbf{I}, \mathbf{C})$
\end{algorithmic}
\vspace{1mm}\hrule
\end{document}
"""

alg2_tex = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb,algorithmicx,algpseudocode}
\begin{document}
\noindent\textbf{Algorithm 2: VisioCrypt Volume-Hiding Search Protocol}
\vspace{1mm}\hrule\vspace{1mm}
\begin{algorithmic}[1]
\Require Keyword $w$, state table $\mathbf{\Sigma}$, client master key $K$
\Ensure Decrypted matching document IDs $R_w$
\State \textbf{Client Phase (Dart Background Isolate):}
\State $(v_w, c_w) \leftarrow \mathbf{\Sigma}[w]$; $T_w \leftarrow \text{HMAC}(K_{\text{search}}, w \parallel v_w)$
\State \textbf{InjectQueryDelay}() \Comment{Smooth network burstiness}
\State Send $T_w$ to Cloud Storage Server
\State \textbf{Server Phase (Untrusted Cloud):}
\State $(iv \parallel E_w) \leftarrow \mathbf{I}[T_w]$; Send $(iv \parallel E_w)$ to Client
\State \textbf{Client Result Resolution Phase:}
\State $L_w^* \leftarrow \text{AES-GCM-Dec}(K_{\text{index}}, iv, E_w)$
\State $R_w \leftarrow \emptyset$
\For{each identifier $id \in L_w^*$}
    \If{$id \ne \text{DUMMY} \land \mathbf{BF}\text{.Contains}(w \parallel id) = \text{False}$}
        \State $R_w \leftarrow R_w \cup \{id\}$
    \EndIf
\EndFor
\State \textbf{ZeroizeMemory}($\{K_{\text{search}}, K_{\text{index}}, L_w^*\})$
\State \Return $R_w$
\end{algorithmic}
\vspace{1mm}\hrule
\end{document}
"""

alg3_tex = r"""\documentclass[preview,varwidth=88mm]{standalone}
\usepackage{amsmath,amsfonts,amssymb,algorithmicx,algpseudocode}
\begin{document}
\noindent\textbf{Algorithm 3: VisioCrypt Dynamic Incremental Update}
\vspace{1mm}\hrule\vspace{1mm}
\begin{algorithmic}[1]
\Require Operation $op \in \{\text{ADD}, \text{DEL}\}$, document $D_j$, client key $K$
\State $(K_{\text{enc}}, K_{\text{search}}, K_{\text{index}}, K_{\text{update}}) \leftarrow \text{HKDF-Expand}(K)$
\State $\mathbf{W}_j \leftarrow \text{ExtractKeywords}(D_j)$
\For{each keyword $w \in \mathbf{W}_j$}
    \If{$op = \text{DEL}$}
        \State $\mathbf{BF}\text{.Insert}(w \parallel docId(D_j))$ \Comment{Local Bloom filter}
    \Else
        \State $(v_w, c_w) \leftarrow \mathbf{\Sigma}[w]$; $v_w' \leftarrow v_w + 1$; $\mathbf{\Sigma}[w] \leftarrow (v_w', c_w + 1)$
        \State $T_w' \leftarrow \text{HMAC}(K_{\text{search}}, w \parallel v_w')$
        \State Encrypt and send updated candidate bucket $\mathbf{I}[T_w']$
    \EndIf
\EndFor
\State \textbf{ZeroizeMemory}($\{K_{\text{enc}}, K_{\text{search}}, K_{\text{index}}, K_{\text{update}}\}$)
\end{algorithmic}
\vspace{1mm}\hrule
\end{document}
"""

algs = {"alg_build": alg_tex, "alg_search": alg2_tex, "alg_update": alg3_tex}

for name, src in algs.items():
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
