import os, subprocess
import fitz  # PyMuPDF

os.chdir(r"e:\_PROJECTS\visiocrypto\writing_paper")

# Standalone tex templates for tables and listings
items = {
    "tab_comparison": r"""\documentclass[preview,varwidth=180mm]{standalone}
\usepackage{booktabs,amsmath,amsfonts,amssymb}
\begin{document}
\begin{table*}[t]
\centering
\small
\begin{tabular}{lcccccccc}
\toprule
\textbf{Scheme} & \textbf{Year} & \textbf{Search Complexity} & \textbf{Dynamic (Add/Del)} & \textbf{Forward Privacy} & \textbf{Backward Privacy} & \textbf{Volume Hiding} & \textbf{RAM Zeroization} & \textbf{TEE Anchor} \\ \midrule
Song et al. & 2000 & $\mathcal{O}(N)$ Linear Scan & No & No & No & No & No & No \\
Curtmola et al. & 2006 & $\mathcal{O}(|L_w|)$ Sub-linear & Static & No & No & No & No & No \\
Kamara et al. & 2012 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & No & No & No & No & No \\
Cash et al. & 2013 & $\mathcal{O}(|L_w|)$ Sub-linear & Static & No & No & No & No & No \\
Sophos (Bost) & 2016 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes (Add only) & Yes & No & No & No & No \\
Diana (Bost et al.) & 2017 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Yes & Type-II & No & No & No \\
SEAL (Demertzis et al.) & 2020 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Yes & Type-II & Heuristic & No & No \\
Patel et al. & 2023 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Yes & Type-II & Yes (Static/Bin) & No & No \\
SWAT (Ihsan et al.) & 2024 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Heuristic & No & Tunable & No & No \\
VisioLock & 2026 & $\mathcal{O}(1)$ Audio-Domain & Static & N/A & N/A & N/A & Yes (Client) & Device-Bound \\
\textbf{VisioCrypt (Ours)} & \textbf{2026} & $\mathbf{\mathcal{O}(|L_w|)}$ \textbf{Sub-linear} & \textbf{Yes} & \textbf{Yes} & \textbf{Type-II} & \textbf{Yes (Power-of-Two)} & \textbf{Yes (Active RAM Wipe)} & \textbf{ARM TrustZone} \\ \bottomrule
\end{tabular}
\end{table*}
\end{document}
""",

    "tab_testbed": r"""\documentclass[preview,varwidth=90mm]{standalone}
\usepackage{booktabs,amsmath,amsfonts,amssymb}
\begin{document}
\begin{table}[h]
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
\textbf{Tier} & \textbf{Device Model} & \textbf{SoC Processor} & \textbf{RAM / Storage} & \textbf{Android OS} \\ \midrule
Tier 1 & Xiaomi Redmi K80 & Snapdragon 8 Gen 3 & 16 GB LPDDR5X / UFS 4.0 & Android 14 \\
Tier 2 & Redmi Turbo 4 Pro & Snapdragon 8s Gen 4 & 12 GB LPDDR5X / UFS 4.0 & Android 14 \\
Tier 3 & Google Pixel 7a & Google Tensor G2 & 8 GB LPDDR5 / UFS 3.1 & Android 14 \\
Tier 4 & Samsung Galaxy A14 & MediaTek Helio G88 & 4 GB LPDDR4X / eMMC 5.1 & Android 13 \\ \bottomrule
\end{tabular}
\end{table}
\end{document}
""",

    "tab_throughput": r"""\documentclass[preview,varwidth=90mm]{standalone}
\usepackage{booktabs,amsmath,amsfonts,amssymb}
\begin{document}
\begin{table}[h]
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
\textbf{Cipher Architecture} & \textbf{Tier 1 (K80)} & \textbf{Tier 2 (Turbo 4)} & \textbf{Tier 3 (Pixel 7a)} & \textbf{Tier 4 (A14)} \\ \midrule
AES-GCM-256 & $248.60 \pm 5.1$ & $215.40 \pm 4.5$ & $112.60 \pm 3.1$ & $48.20 \pm 1.8$ \\
\textbf{AES-CTR-256 + HMAC} & $\mathbf{310.50 \pm 3.8}$ & $\mathbf{265.20 \pm 3.4}$ & $\mathbf{142.80 \pm 2.6}$ & $\mathbf{68.40 \pm 1.9}$ \\ \bottomrule
\end{tabular}
\end{table}
\end{document}
""",

    "tab_latency": r"""\documentclass[preview,varwidth=90mm]{standalone}
\usepackage{booktabs,amsmath,amsfonts,amssymb}
\begin{document}
\begin{table}[h]
\centering
\footnotesize
\begin{tabular}{lcccc}
\toprule
\textbf{Search Architecture} & \textbf{Tier 1 (K80)} & \textbf{Tier 2 (Turbo 4)} & \textbf{Tier 3 (Pixel 7a)} & \textbf{Tier 4 (A14)} \\ \midrule
Linear Scanning & $3420.00 \text{ ms}$ & $4150.00 \text{ ms}$ & $8420.00 \text{ ms}$ & $18650.00 \text{ ms}$ \\
SQLCipher Database & $5.20 \text{ ms}$ & $6.80 \text{ ms}$ & $14.20 \text{ ms}$ & $34.80 \text{ ms}$ \\
Unpadded Hash Index & $0.21 \text{ ms}$ & $0.26 \text{ ms}$ & $0.58 \text{ ms}$ & $1.42 \text{ ms}$ \\
\textbf{VisioCrypt} & $\mathbf{0.23 \text{ ms}}$ & $\mathbf{0.29 \text{ ms}}$ & $\mathbf{0.62 \text{ ms}}$ & $\mathbf{1.48 \text{ ms}}$ \\ \bottomrule
\end{tabular}
\end{table}
\end{document}
""",

    "tab_storage_energy": r"""\documentclass[preview,varwidth=90mm]{standalone}
\usepackage{booktabs,amsmath,amsfonts,amssymb}
\begin{document}
\begin{table}[h]
\centering
\footnotesize
\begin{tabular}{rcccc}
\toprule
\textbf{Keywords} & \textbf{Unpadded Size} & \textbf{Padded Size} & \textbf{Inflation} & \textbf{Energy / 1K Queries} \\ \midrule
100 Keywords & 14.2 KB & 21.8 KB & $+53.5\%$ & $0.18\text{ mJ}$ \\
1,000 Keywords & 145.0 KB & 218.5 KB & $+50.7\%$ & $0.54\text{ mJ}$ \\
10,000 Keywords & 1.48 MB & 2.21 MB & $+49.3\%$ & $1.85\text{ mJ}$ \\ \bottomrule
\end{tabular}
\end{table}
\end{document}
""",

    "lst_isolate": r"""\documentclass[preview,varwidth=90mm]{standalone}
\usepackage{listings,xcolor}
\definecolor{codegreen}{rgb}{0,0.6,0}
\definecolor{codegray}{rgb}{0.5,0.5,0.5}
\definecolor{codepurple}{rgb}{0.58,0,0.82}
\definecolor{backcolour}{rgb}{0.96,0.96,0.96}
\lstdefinestyle{mystyle}{
    backgroundcolor=\color{backcolour},   
    commentstyle=\color{codegreen},
    keywordstyle=\color{magenta},
    numberstyle=\tiny\color{codegray},
    stringstyle=\color{codepurple},
    basicstyle=\ttfamily\scriptsize,
    breakatwhitespace=false,         
    breaklines=true,                 
    captionpos=b,                    
    keepspaces=true,                 
    numbers=left,                    
    numbersep=5pt,                  
    showspaces=false,                
    showstringspaces=false,
    showtabs=false,                  
    tabsize=2
}
\lstset{style=mystyle}
\begin{document}
\begin{lstlisting}[language=Java]
static void _isolateEntryPoint(IsolateMsg msg) async {
  final keys = SseEngine.deriveKeys(msg.key, msg.salt);
  final kSearch = keys['kSearch']!, kVal = keys['kVal']!;
  final words = await SseEngine.extractWords(File(msg.path));
  final Map<String, Uint8List> indexDb = {};
  for (final w in words) {
    final t_w = SseEngine.computeTrapdoor(w, kSearch);
    final padded = SseEngine.padList([msg.docId]);
    final iv = Uint8List(12);
    final c_w = SseEngine.encryptGcm(kVal, iv, padded);
    indexDb[t_w] = Uint8List.fromList([...iv, ...c_w]);
  }
  // Active byte array zeroization (RAM wipe)
  kSearch.fillRange(0, kSearch.length, 0);
  kVal.fillRange(0, kVal.length, 0);
  msg.key.fillRange(0, msg.key.length, 0);
  msg.port.send({'status': 'done', 'index': indexDb});
}
\end{lstlisting}
\end{document}
"""
}

for name, src in items.items():
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
