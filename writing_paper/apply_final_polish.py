import os

tex_path = r"e:\_PROJECTS\visiocrypto\writing_paper\paper_ieee.tex"
with open(tex_path, "r", encoding="utf-8") as f:
    tex = f.read()

replacements = [
    # Intro
    (
        "However, the server still sees how many files match each keyword.",
        "Unfortunately, cloud servers still count how many files match each search."
    ),
    (
        "We track file additions and deletions locally on the phone to preserve forward and backward privacy.",
        "We track new and deleted files locally so the cloud learns nothing about updates."
    ),
    # Related Work
    (
        "Cash designed algorithms to handle large boolean search queries \\cite{cash2013}.",
        "Cash made boolean queries fast across large indexes \\cite{cash2013}."
    ),
    (
        "Even with encrypted indexes, servers learn the exact number of matching files. Watching search match counts lets attackers reconstruct full databases \\cite{islam2012,cash2015leakage,kellaris2016,gui2019volume,kornaropoulos2020}.",
        "Watching search match counts lets attackers reconstruct full databases \\cite{islam2012,cash2015leakage,kellaris2016,gui2019volume,kornaropoulos2020}."
    ),
    (
        "Sophos added forward privacy to keep newly added files hidden from older queries \\cite{bost2016sophos}.",
        "Sophos added forward privacy so old queries never find newly added files \\cite{bost2016sophos}."
    ),
    (
        "We manage file additions and deletions on the handset using version tags and a Bloom filter.",
        "Our phone tracks file updates locally using version counters and a Bloom filter."
    ),
    # Architecture enum
    (
        r"""\begin{enumerate}
    \item \textbf{Mobile Client}: The phone stores the master secret inside ARM TrustZone and runs isolated workers for encryption and memory wiping.
    \item \textbf{Network Channel}: Our network channel adds tiny random pauses to hide traffic timing.
    \item \textbf{Cloud Storage Server}: The cloud server holds encrypted index tables and encrypted files.
\end{enumerate}""",
        r"""\begin{enumerate}
    \item \textbf{Mobile Client}: Our phone keeps the root key inside ARM TrustZone and runs isolated encryption workers.
    \item \textbf{Network Channel}: Our network channel inserts tiny random delays to hide traffic patterns.
    \item \textbf{Cloud Storage Server}: The cloud holds our encrypted index entries and document ciphertexts.
\end{enumerate}"""
    ),
    # Syntax
    (
        "Our encrypted search scheme uses six core operations.",
        "We build our encrypted search scheme around six operations."
    ),
    # Evaluation
    (
        "We ran network tests with simulated packet sniffing to check query delay buffers. Adding random pauses between $10$ and $50\\text{ ms}$ smooths out bursty traffic, making search bursts indistinguishable from normal background pings. These small delays feel instantaneous during normal daily searches.",
        "We monitored network packets to make sure query delays hide bursty traffic. Pausing 10 to 50 milliseconds between lookups smooths out bursty traffic. Mobile users barely notice these tiny pauses during daily searches."
    ),
    # Conclusion
    (
        "VisioCrypt gives smartphone users private encrypted search without leaking query match counts.",
        "Our scheme brings volume-hiding encrypted search to mobile phones without leaking match counts."
    )
]

for src, dst in replacements:
    if src in tex:
        tex = tex.replace(src, dst)
        print("Replaced chunk successfully!")
    else:
        print("WARNING: chunk not found:", src[:40])

with open(tex_path, "w", encoding="utf-8") as f:
    f.write(tex)
print("Updated paper_ieee.tex with final green sentences!")
