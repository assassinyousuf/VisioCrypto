import os, sys

tex_path = r"e:\_PROJECTS\visiocrypto\writing_paper\paper_ieee.tex"
with open(tex_path, "r", encoding="utf-8") as f:
    tex = f.read()

# Apply all humanized improvements
replacements = [
    # Introduction
    (
        "To test real performance, we ran lookups on four physical phones, keeping search latencies under a single millisecond without draining the battery.",
        "We tested lookups on four real phones, getting sub-millisecond results with barely any battery use."
    ),
    # Section III-C Syntax
    (
        r"""\subsection{Formal Syntax of DVH-SSE.}
A Dynamic Volume-Hiding Searchable Symmetric Encryption ($\text{DVH-SSE}$) scheme consists of six core algorithms:
\begin{itemize}
    \item $\text{KeyGen}(1^k) \to K$: Generates master secret $K$ inside the phone secure enclave.
    \item $\text{BuildIndex}(\mathbf{D}, K) \to (\mathbf{I}, \mathbf{C}, \mathbf{BF})$: Creates an encrypted multi-map $\mathbf{I}$, ciphertext repository $\mathbf{C}$, and local deletion filter $\mathbf{BF}$.
    \item $\text{Trapdoor}(w, v_w, K) \to T_w$: Computes search token $T_w$ from keyword $w$ and version $v_w$.
    \item $\text{Search}(\mathbf{I}, T_w) \to (iv \parallel E_w)$: Looks up the encrypted candidate bucket corresponding to $T_w$.
    \item $\text{Update}(op, D_j, K, \mathbf{BF}) \to (\mathbf{R}_{\text{delta}}, \mathbf{BF}')$: Logs encrypted delta update $\mathbf{R}_{\text{delta}}$ and updates local Bloom filter state.
    \item $\text{Dec}(C_i, K) \to D_i$: Restores ciphertext $C_i$ back to plaintext document $D_i$.
\end{itemize}""",
        r"""\subsection{Formal Syntax of DVH-SSE.}
A volume-hiding searchable encryption scheme consists of six core algorithms.
Key generation creates master secrets inside the phone hardware enclave.
We make an encrypted search table and a local filter on the phone.
Trapdoors turn keywords into encrypted search tags.
Search finds the matching bucket on the remote server.
File changes get written to encrypted delta records and tracked in our filter.
Decryption turns downloaded ciphertexts back into plain files on the phone."""
    ),
    # Section IV-B Padding policy
    (
        r"""\subsection{Power-of-Two Volume-Hiding Padding Policy.}
To eliminate match count leakage, the phone pads each document list with dummy IDs up to the next power of two:
\begin{equation}
|\text{Pad}(L_w)| = \max\left(4, 2^{\lceil \log_2 (|L_w|) \rceil}\right)
\end{equation}
Every padded list has at least four entries so rare words stay hidden, padding with dummy values $\text{DUMMY} = 0\text{xFFFFFFFF}$. As illustrated in Figure \ref{fig:padding}, the cloud server observes only uniform bucket sizes $\{4, 8, 16, 32, 64, \dots\}$, collapsing statistical frequency distinctions between rare and frequent terms.""",
        r"""\subsection{Power-of-Two Volume-Hiding Padding Policy.}
To stop match count leakage, the phone pads candidate lists to powers of two. We add dummy entries so every result list has four, eight, sixteen, or thirty-two items. Rare words stay hidden because list sizes look identical across terms.
\begin{equation}
|\text{Pad}(L_w)| = \max\left(4, 2^{\lceil \log_2 (|L_w|) \rceil}\right)
\end{equation}
This completely hides exact match counts from the remote server. The cloud server observes only uniform bucket sizes of four, eight, sixteen, or thirty-two items."""
    ),
    # Section IV-D Bloom filter
    (
        r"""\subsection{Dynamic Deletion Handling via Local Bloom Filter.}
Deleted files get recorded in a local phone filter $\mathbf{BF}$ without alerting the cloud server. For a target capacity of $n = 50,000$ deleted keyword pairs and a false positive probability $p = 10^{-4}$, the required bit length $m$ and hash count $k$ are:
\begin{equation}
m = -\frac{n \ln p}{(\ln 2)^2} \approx 117 \text{ KB}, \quad k = \frac{m}{n} \ln 2 \approx 13
\end{equation}
Our Bloom filter parameters keep false positive rates below one in ten thousand, allowing client devices to filter deleted files in under $0.05\text{ ms}$ with negligible RAM overhead.""",
        r"""\subsection{Dynamic Deletion Handling via Local Bloom Filter.}
Deleted files get recorded in a local phone filter $\mathbf{BF}$ without alerting the cloud server. For $n = 50,000$ deleted keyword pairs and error rate $p = 10^{-4}$:
\begin{equation}
m = -\frac{n \ln p}{(\ln 2)^2} \approx 117 \text{ KB}, \quad k = \frac{m}{n} \ln 2 \approx 13
\end{equation}
Our Bloom filter parameters keep false positive rates below one in ten thousand. This allows client devices to filter deleted files in under $0.05\text{ ms}$ with negligible RAM overhead."""
    ),
    # Section VI Android Heap
    (
        "Discarded key bytes can sit in physical RAM for minutes before getting reclaimed, exposing plaintext keys to cold-boot attacks.",
        "Discarded key bytes can sit in physical RAM for minutes before getting reclaimed."
    ),
    (
        r"We store keys inside plain byte lists and zero out the entire buffer the moment cipher operations finish using `.fillRange(0, len, 0)`.",
        "We store keys inside plain byte lists and zero out the entire buffer the moment cipher operations finish."
    ),
    # Section VII Evaluation
    (
        "Our benchmark suite evaluates end-to-end symmetric encryption throughput, RAM secret key persistence, search latency, index storage inflation, and battery energy overhead.",
        "We measured encryption throughput and battery draw across our four test phones."
    ),
    (
        r"Figure \ref{fig:throughput} contrasts VisioCrypt's immediate zeroization ($< 1\text{ ms}$) against standard GC retention curves ($> 150\text{ s}$).",
        r"Figure \ref{fig:throughput} shows our instant RAM wipe versus long garbage collection delays."
    ),
    (
        r"Our in-memory filter verified over $22,000$ keyword tags each millisecond on the K80.",
        r"Our in-memory filter verified over twenty-two thousand keyword tags each millisecond on the K80."
    ),
    (
        "We ran network tests with simulated packet sniffing to check query delay buffers. Adding random pauses between $10$ and $50\text{ ms}$ smooths out bursty traffic, making search bursts indistinguishable from normal background pings. These small delays feel instantaneous during normal daily searches.",
        r"We watched network packets to make sure random delay buffers mask search bursts. Pausing 10 to 50 milliseconds between lookups smooths out bursty traffic. Users barely notice these tiny pauses during normal searches."
    ),
    (
        r"Table \ref{tab:storage_energy} tracks file inflation and power use across different dataset sizes. Expanding 10,000 terms into power-of-two buckets increased the index size from 1.48 MB to 2.21 MB ($+49.3\%$). An index of ten thousand keywords takes 2.2 megabytes, easily fitting on modern flash storage. On the budget Galaxy A14, $1,000$ full searches use roughly $1.85\text{ mJ}$ of power. A typical phone battery hardly registers this draw even after weeks of constant searching.",
        r"Table \ref{tab:storage_energy} shows our test numbers. Padding 10,000 terms to powers of two made the index grow from 1.48 MB to 2.21 MB. This index easily fits on the phone. Running 1,000 searches on our budget phone used just $1.85\text{ mJ}$ of battery energy. A typical phone battery hardly registers this draw even after weeks of constant searching."
    ),
    (
        "Cold lookups added under $0.12\text{ ms}$ of extra delay across all four phones. This confirms that reading small encrypted chunks from flash storage never bottlenecks search speed. Firing 100 rapid queries back-to-back showed completely flat memory usage. The background isolate easily processes consecutive requests without dropping frames on the main user interface thread.",
        r"Cold searches added under 0.12 milliseconds of delay across our four test phones. Reading encrypted blocks from flash storage never created a bottleneck for our lookups. Firing 100 rapid queries back-to-back showed completely flat memory usage. Our background worker handles rapid queries without causing UI stutter."
    ),
    # Section VIII Discussion
    (
        "Padding candidate lists trades a small amount of extra bandwidth for solid query privacy. Using power-of-two buckets conceals match counts while adding roughly fifty percent extra data. For massive collections with millions of files, users can pick wider bucket intervals to keep data transfer reasonable. Because VisioCrypt operates purely on the client, standard cloud storage backends like S3, Google Drive, or personal servers work without modifications.",
        r"We send a little extra data to protect search privacy. Power-of-two padding hides search volumes with about fifty percent storage inflation. For huge libraries, users can choose wider bucket steps to save mobile data. Since our app runs purely on the handset, standard cloud storage backends like S3 work out of the box."
    ),
    (
        "We send occasional dummy queries to disrupt co-occurrence trackers. These background requests blend in with normal searches so eavesdroppers cannot pinpoint when someone actually looks up a receipt. Our app hooks into the Android Keystore system with biometric fingerprint prompts. This prevents physical intruders from grabbing root keys even on rooted handsets.",
        r"Sending occasional dummy requests stops observers from timing real searches. Our app hooks into the Android Keystore system with biometric fingerprint prompts. This keeps master keys safe from extraction even on rooted phones."
    ),
    (
        "Locking root keys inside TrustZone stops intruders from stealing them, while wiping key bytes from RAM immediately protects active sessions from memory dumping attacks.",
        r"The phone clears key arrays from RAM the moment encryption finishes, while our root key stays locked inside ARM TrustZone behind a fingerprint sensor."
    ),
    # Section IX Conclusion
    (
        "VisioCrypt lets mobile users search encrypted cloud backups without leaking query volumes. Padding match counts to powers of two stops cloud admins from guessing search terms. Our security proof confirms that search traces leak no keyword information. Our real-world phone tests show searches complete in under two milliseconds.",
        r"VisioCrypt gives smartphone users private encrypted search without leaking query match counts. Padding match counts to powers of two stops cloud admins from guessing search terms. Our security proof confirms that search traces leak no keyword information. Our phone tests showed search lookups finish in under a millisecond with negligible battery use."
    )
]

for orig, rep in replacements:
    if orig in tex:
        tex = tex.replace(orig, rep)
        print(f"Replaced successfully: {orig[:40]}...")
    else:
        print(f"NOT FOUND: {orig[:40]}...")

with open(tex_path, "w", encoding="utf-8") as f:
    f.write(tex)
print("Updated paper_ieee.tex successfully!")
