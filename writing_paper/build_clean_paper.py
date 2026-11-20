import os

tex_path = r"e:\_PROJECTS\visiocrypto\writing_paper\paper_ieee.tex"
with open(tex_path, "r", encoding="utf-8") as f:
    tex = f.read()

# Replace Table 1
tab1_orig = r"""\begin{table*}[t]
\centering
\caption{Qualitative Comparison of Searchable Symmetric Encryption Schemes.}
\label{tab:comparison}
\resizebox{\textwidth}{!}{%
\begin{tabular}{lcccccccc}
\toprule
\textbf{Scheme} & \textbf{Year} & \textbf{Search Complexity} & \textbf{Dynamic (Add/Del)} & \textbf{Forward Privacy} & \textbf{Backward Privacy} & \textbf{Volume Hiding} & \textbf{RAM Zeroization} & \textbf{TEE Anchor} \\ \midrule
Song et al. \cite{song2000} & 2000 & $\mathcal{O}(N)$ Linear Scan & No & No & No & No & No & No \\
Curtmola et al. \cite{curtmola2006} & 2006 & $\mathcal{O}(|L_w|)$ Sub-linear & Static & No & No & No & No & No \\
Kamara et al. \cite{kamara2012} & 2012 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & No & No & No & No & No \\
Cash et al. \cite{cash2013} & 2013 & $\mathcal{O}(|L_w|)$ Sub-linear & Static & No & No & No & No & No \\
Sophos (Bost) \cite{bost2016sophos} & 2016 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes (Add only) & Yes & No & No & No & No \\
Diana (Bost et al.) \cite{bost2017diana} & 2017 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Yes & Type-II & No & No & No \\
SEAL (Demertzis et al.) \cite{demertzis2020seal} & 2020 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Yes & Type-II & Heuristic & No & No \\
Patel et al. \cite{patel2023dvh} & 2023 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Yes & Type-II & Yes (Static/Bin) & No & No \\
SWAT (Ihsan et al.) \cite{swat2024} & 2024 & $\mathcal{O}(|L_w|)$ Sub-linear & Yes & Heuristic & No & Tunable & No & No \\
VisioLock \cite{hossain2026visiolock} & 2026 & $\mathcal{O}(1)$ Audio-Domain & Static & N/A & N/A & N/A & Yes (Client) & Device-Bound \\
\textbf{VisioCrypt (Ours)} & \textbf{2026} & $\mathbf{\mathcal{O}(|L_w|)}$ \textbf{Sub-linear} & \textbf{Yes} & \textbf{Yes} & \textbf{Type-II} & \textbf{Yes (Power-of-Two)} & \textbf{Yes (Active RAM Wipe)} & \textbf{ARM TrustZone} \\ \bottomrule
\end{tabular}%
}
\end{table*}"""

tab1_rep = r"""\begin{table*}[t]
\centering
\caption{Qualitative Comparison of Searchable Symmetric Encryption Schemes.}
\label{tab:comparison}
\includegraphics[width=\textwidth]{figures/tab_comparison.png}
\end{table*}"""

# Replace Algorithms 1, 2, 3
algs_orig = r"""\begin{algorithm}[t]
\caption{VisioCrypt Index Construction ($\text{BuildIndex}$)}
\label{alg:build}
\begin{algorithmic}[1]
\Require Plaintext Documents $\mathbf{D}$, Master Secret $K$
\Ensure Encrypted Index $\mathbf{I}$, Ciphertexts $\mathbf{C}$, Bloom Filter $\mathbf{BF}$
\State $(K_{\text{enc}}, K_{\text{search}}, K_{\text{index}}, K_{\text{update}}) \leftarrow \text{HKDF-SHA256}(K)$
\State $\mathbf{I} \leftarrow \emptyset$, \quad $\mathbf{BF} \leftarrow \text{NewFilter}()$
\For{each document $D_i \in \mathbf{D}$}
    \State $C_i \leftarrow \text{AES-CTR-256}_{K_{\text{enc}}}(D_i) \parallel \text{HMAC-SHA256}(C_i)$
    \State Extract unique words $\mathbf{W}_i \leftarrow \text{Tokenize}(D_i)$
    \For{each word $w \in \mathbf{W}_i$}
        \State Append document identifier $i$ to map $\mathbf{W}_{\text{map}}[w]$
    \EndFor
\EndFor
\For{each keyword $w \in \mathbf{W}_{\text{map}}.\text{keys}()$}
    \State $T_w \leftarrow \text{HMAC-SHA256}_{K_{\text{search}}}(w)$
    \State $L'_w \leftarrow \text{Pad}(\mathbf{W}_{\text{map}}[w])$
    \State $P_w \leftarrow \text{Pack}(L'_w)$
    \State Choose random 12-byte initialization vector $iv$
    \State $E_w \leftarrow \text{AES-GCM-256-Enc}_{K_{\text{index}}}(iv, P_w)$
    \State Store entry $\mathbf{I}[T_w] \leftarrow (iv \parallel E_w)$
\EndFor
\State Clear memory $(K_{\text{enc}}, K_{\text{search}}, K_{\text{index}}, K_{\text{update}})$
\State \Return $(\mathbf{I}, \mathbf{C}, \mathbf{BF})$
\end{algorithmic}
\end{algorithm}

\begin{algorithm}[t]
\caption{VisioCrypt Search Query Resolution ($\text{Search}$)}
\label{alg:search}
\begin{algorithmic}[1]
\Require Index $\mathbf{I}$, Keyword $w$, Version $v_w$, Key $K_{\text{index}}$, Filter $\mathbf{BF}$
\Ensure Matching document identifiers
\State $T_w \leftarrow \text{HMAC-SHA256}_{K_{\text{search}}}(w)$
\If{$T_w \notin \mathbf{I}$}
    \State \Return $\emptyset$
\EndIf
\State Parse $(iv \parallel E_w) \leftarrow \mathbf{I}[T_w]$
\State $P_w \leftarrow \text{AES-GCM-256-Dec}_{K_{\text{index}}}(iv, E_w)$
\If{Authentication Check Fails}
    \State \Return $\bot$
\EndIf
\State $L'_w \leftarrow \text{Unpack}(P_w)$
\State $\text{Matches} \leftarrow \{id \in L'_w \mid id \neq \text{DUMMY} \land \neg \mathbf{BF}.\text{Test}(w \parallel id)\}$
\State Clear memory $K_{\text{index}}$
\State \Return $\text{Matches}$
\end{algorithmic}
\end{algorithm}

\begin{algorithm}[t]
\caption{VisioCrypt Dynamic Incremental Update ($\text{Update}$)}
\label{alg:update}
\begin{algorithmic}[1]
\Require Mode $op \in \{\text{add},\text{del}\}$, File $D_j$, Table $\mathbf{V}$, Key $K_{\text{update}}$, $\mathbf{BF}$
\Ensure Encrypted Delta $\mathbf{R}_{\text{delta}}$, Filter $\mathbf{BF}'$
\State Extract unique words $\mathbf{W}_j \leftarrow \text{Tokenize}(D_j)$
\State $\mathbf{R}_{\text{delta}} \leftarrow \emptyset$
\For{each word $w \in \mathbf{W}_j$}
    \State $\mathbf{V}[w] \leftarrow \mathbf{V}[w] + 1$
    \State $T_{w,\text{dyn}} \leftarrow \text{HMAC-SHA256}_{K_{\text{search}}}(w \parallel \mathbf{V}[w])$
    \If{$op == \text{del}$}
        \State $\mathbf{BF}.\text{Insert}(w \parallel \text{DocID}(D_j))$
    \EndIf
    \State $iv \xleftarrow{\$} \{0,1\}^{96}$
    \State $E_w \leftarrow \text{AES-GCM-Enc}_{K_{\text{update}}}(iv, (op, \text{DocID}(D_j)))$
    \State Append $(T_{w,\text{dyn}}, iv \parallel E_w)$ to list $\mathbf{R}_{\text{delta}}$
\EndFor
\State Clear memory $K_{\text{update}}$
\State \Return $(\mathbf{R}_{\text{delta}}, \mathbf{BF})$
\end{algorithmic}
\end{algorithm}"""

algs_rep = r"""\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/alg_build.png}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/alg_search.png}
\end{figure}

\begin{figure}[t]
\centering
\includegraphics[width=\columnwidth]{figures/alg_update.png}
\end{figure}"""

# Replace Listing 1
lst1_orig = r"""\begin{lstlisting}[language=Java, label=lst:isolate, caption={Isolate Routine and Memory Zeroization.}]
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
\end{lstlisting}"""

lst1_rep = r"""\begin{figure}[h]
\centering
\includegraphics[width=\columnwidth]{figures/lst_isolate.png}
\caption{Isolate Routine and Memory Zeroization.}
\label{lst:isolate}
\end{figure}"""

# Replace Table II
tab2_orig = r"""\begin{table}[h]
\centering
\caption{Hardware Testbed Device Profiles.}
\label{tab:testbed}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccc}
\toprule
\textbf{Tier} & \textbf{Device Model} & \textbf{SoC Processor} & \textbf{RAM / Storage} & \textbf{Android OS} \\ \midrule
Tier 1 & Xiaomi Redmi K80 & Snapdragon 8 Gen 3 & 16 GB LPDDR5X / UFS 4.0 & Android 14 \\
Tier 2 & Redmi Turbo 4 Pro & Snapdragon 8s Gen 4 & 12 GB LPDDR5X / UFS 4.0 & Android 14 \\
Tier 3 & Google Pixel 7a & Google Tensor G2 & 8 GB LPDDR5 / UFS 3.1 & Android 14 \\
Tier 4 & Samsung Galaxy A14 & MediaTek Helio G88 & 4 GB LPDDR4X / eMMC 5.1 & Android 13 \\ \bottomrule
\end{tabular}%
}
\end{table}"""

tab2_rep = r"""\begin{table}[h]
\centering
\caption{Hardware Testbed Device Profiles.}
\label{tab:testbed}
\includegraphics[width=\columnwidth]{figures/tab_testbed.png}
\end{table}"""

# Replace Table III
tab3_orig = r"""\begin{table}[h]
\centering
\caption{Symmetric File Encryption Throughput (MB/\lowercase{s}).}
\label{tab:throughput}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccc}
\toprule
\textbf{Cipher Architecture} & \textbf{Tier 1 (K80)} & \textbf{Tier 2 (Turbo 4)} & \textbf{Tier 3 (Pixel 7a)} & \textbf{Tier 4 (A14)} \\ \midrule
AES-GCM-256 & $248.60 \pm 5.1$ & $215.40 \pm 4.5$ & $112.60 \pm 3.1$ & $48.20 \pm 1.8$ \\
\textbf{AES-CTR-256 + HMAC} & $\mathbf{310.50 \pm 3.8}$ & $\mathbf{265.20 \pm 3.4}$ & $\mathbf{142.80 \pm 2.6}$ & $\mathbf{68.40 \pm 1.9}$ \\ \bottomrule
\end{tabular}%
}
\end{table}"""

tab3_rep = r"""\begin{table}[h]
\centering
\caption{Symmetric File Encryption Throughput (MB/\lowercase{s}).}
\label{tab:throughput}
\includegraphics[width=\columnwidth]{figures/tab_throughput.png}
\end{table}"""

# Replace Table IV
tab4_orig = r"""\begin{table}[h]
\centering
\caption{Multi-Device Search Query Latency ($N = 10,000$ Keywords).}
\label{tab:latency}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccc}
\toprule
\textbf{Search Architecture} & \textbf{Tier 1 (K80)} & \textbf{Tier 2 (Turbo 4)} & \textbf{Tier 3 (Pixel 7a)} & \textbf{Tier 4 (A14)} \\ \midrule
Linear Scanning & $3420.00 \text{ ms}$ & $4150.00 \text{ ms}$ & $8420.00 \text{ ms}$ & $18650.00 \text{ ms}$ \\
SQLCipher Database & $5.20 \text{ ms}$ & $6.80 \text{ ms}$ & $14.20 \text{ ms}$ & $34.80 \text{ ms}$ \\
Unpadded Hash Index & $0.21 \text{ ms}$ & $0.26 \text{ ms}$ & $0.58 \text{ ms}$ & $1.42 \text{ ms}$ \\
\textbf{VisioCrypt} & $\mathbf{0.23 \text{ ms}}$ & $\mathbf{0.29 \text{ ms}}$ & $\mathbf{0.62 \text{ ms}}$ & $\mathbf{1.48 \text{ ms}}$ \\ \bottomrule
\end{tabular}%
}
\end{table}"""

tab4_rep = r"""\begin{table}[h]
\centering
\caption{Multi-Device Search Query Latency ($N = 10,000$ Keywords).}
\label{tab:latency}
\includegraphics[width=\columnwidth]{figures/tab_latency.png}
\end{table}"""

# Replace Table V
tab5_orig = r"""\begin{table}[h]
\centering
\caption{Index Storage Inflation and Mobile Energy Overhead.}
\label{tab:storage_energy}
\resizebox{\columnwidth}{!}{%
\begin{tabular}{rcccc}
\toprule
\textbf{Keywords} & \textbf{Unpadded Size} & \textbf{Padded Size} & \textbf{Inflation} & \textbf{Energy / 1K Queries} \\ \midrule
100 Keywords & 14.2 KB & 21.8 KB & $+53.5\%$ & $0.18\text{ mJ}$ \\
1,000 Keywords & 145.0 KB & 218.5 KB & $+50.7\%$ & $0.54\text{ mJ}$ \\
10,000 Keywords & 1.48 MB & 2.21 MB & $+49.3\%$ & $1.85\text{ mJ}$ \\ \bottomrule
\end{tabular}%
}
\end{table}"""

tab5_rep = r"""\begin{table}[h]
\centering
\caption{Index Storage Inflation and Mobile Energy Overhead.}
\label{tab:storage_energy}
\includegraphics[width=\columnwidth]{figures/tab_storage_energy.png}
\end{table}"""

# Body prose humanizations
prose_changes = [
    (
        "Song, Wagner, and Perrig created searchable encryption in 2000 \\cite{song2000}. In 2006, Curtmola established formal security games for searchable encryption \\cite{curtmola2006}. Dynamic schemes later let users add files without rebuilding the entire index \\cite{kamara2012}. Cash scaled searchable encryption to handle massive boolean queries \\cite{cash2013}.",
        "In 2000, Song pioneered searchable symmetric encryption \\cite{song2000}. In 2006, Curtmola defined formal security models for searchable encryption \\cite{curtmola2006}. Dynamic schemes later allowed file additions without rebuilding the entire index \\cite{kamara2012}. Cash designed algorithms to handle large boolean search queries \\cite{cash2013}."
    ),
    (
        "Yet in all these systems, the server learns how many files match each search. Watching search match counts lets attackers reconstruct full databases \\cite{islam2012,cash2015leakage,kellaris2016,gui2019volume,kornaropoulos2020}. Schemes like SEAL and SWAT tried grouping results into bins to limit volume leakage \\cite{demertzis2020seal,swat2024}. Patel grouped search results into fixed bins to cut down volume leakage \\cite{patel2023dvh}. Our approach rounds candidate lists to powers of two directly on the client handset without needing server hardware enclaves \\cite{sgxse2_2020}.",
        "Even with encrypted indexes, servers learn the exact number of matching files. Watching search match counts lets attackers reconstruct full databases \\cite{islam2012,cash2015leakage,kellaris2016,gui2019volume,kornaropoulos2020}. Schemes like SEAL and SWAT tried grouping results into bins to limit volume leakage \\cite{demertzis2020seal,swat2024}. Patel used fixed bin sizes to hide match counts from servers \\cite{patel2023dvh}. Our scheme rounds search lists to powers of two on the phone without needing cloud enclaves \\cite{sgxse2_2020}."
    ),
    (
        "Sophos introduced forward privacy so new files stay hidden from past queries \\cite{bost2016sophos}. Diana added backward privacy so deleted documents stay hidden from future searches \\cite{bost2017diana}. VisioCrypt handles additions and deletions on mobile phones using versioned tokens and a local Bloom filter.",
        "Sophos added forward privacy to keep newly added files hidden from older queries \\cite{bost2016sophos}. Diana added backward privacy so deleted documents stay hidden from future searches \\cite{bost2017diana}. We manage file additions and deletions on the handset using version tags and a Bloom filter."
    ),
    (
        r"""\begin{enumerate}
    \item \textbf{Mobile Client}: Houses the ARM TrustZone hardware enclave with master secret $K$, biometric gating, and an isolated Dart worker that executes index encryption, padding, Bloom filtering, and active memory zeroization.
    \item \textbf{Network Channel}: Buffers search requests and injects random transmission delays so observers cannot track traffic timing.
    \item \textbf{Cloud Storage Server}: Holds encrypted index entries $\mathbf{I}[T_w] = (iv \parallel E_w)$ and document ciphertexts $\mathbf{C} = \{C_i\}$.
\end{enumerate}""",
        r"""\begin{enumerate}
    \item \textbf{Mobile Client}: The phone stores the master secret inside ARM TrustZone and runs isolated workers for encryption and memory wiping.
    \item \textbf{Network Channel}: Our network channel adds tiny random pauses to hide traffic timing.
    \item \textbf{Cloud Storage Server}: The cloud server holds encrypted index tables and encrypted files.
\end{enumerate}"""
    ),
    (
        "The server runs search routines properly but inspects stored records and query traffic to guess what we are searching for. A thief with physical access to the phone might dump the RAM to steal keys.",
        "The remote server runs search routines properly but inspects stored records to guess what we are searching for. An attacker with physical access to the phone might dump RAM to steal keys."
    ),
    (
        "Our in-memory filter verified over twenty-two thousand keyword tags each millisecond on the K80. Adding fresh deletions took barely $0.08\\text{ ms}$ per term. Even holding $50,000$ discarded tags, the table sits at $117\\text{ KB}$ in RAM. Android never kills our background isolate because this tiny footprint stays way below operating system memory limits.",
        "Our in-memory filter verified over twenty-two thousand keyword tags each millisecond on the K80. Adding fresh deletions took barely $0.08\\text{ ms}$ per term. Even with $50,000$ discarded tags, the table sits at $117\\text{ KB}$ in RAM. Android never kills our background worker because this tiny footprint stays way below operating system memory limits."
    ),
    (
        "Repeated searches naturally hit warm phone memory caches. To measure worst-case lookups, we flushed OS page caches before each test run. Cold searches added under 0.12 milliseconds of delay across our four test phones. Reading encrypted blocks from flash storage never created a bottleneck for our lookups. Firing 100 rapid queries back-to-back showed completely flat memory usage. Our background worker handles rapid queries without causing UI stutter.",
        "Repeated queries naturally pull from warm memory caches. We flushed phone memory caches before each test to measure worst-case cold lookups. Cold searches added under 0.12 milliseconds of delay across our four test phones. Reading encrypted blocks from flash storage never created a bottleneck for our lookups. Firing 100 rapid queries back-to-back showed completely flat memory usage. Our background worker handles rapid queries without causing UI stutter."
    )
]

# Execute replacements
for src, dst in [(tab1_orig, tab1_rep), (algs_orig, algs_rep), (lst1_orig, lst1_rep), (tab2_orig, tab2_rep), (tab3_orig, tab3_rep), (tab4_orig, tab4_rep), (tab5_orig, tab5_rep)] + prose_changes:
    if src in tex:
        tex = tex.replace(src, dst)
        print("Replaced chunk successfully!")
    else:
        print("WARNING: Chunk not found!")

with open(tex_path, "w", encoding="utf-8") as f:
    f.write(tex)
print("Updated paper_ieee.tex with crisp high-res figures and humanized prose!")
