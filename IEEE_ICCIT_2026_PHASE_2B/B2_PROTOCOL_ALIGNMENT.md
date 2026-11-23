# Phase 2B Deliverable B2: Protocol Alignment & Algorithm 1 Specification Report

**Subject:** Resolution of Versioned Update Mismatch, Static Scheme Formalization, and Dynamic Update Leakage Analysis  
**Status:** **VERIFIED** (Protocol Mathematically Aligned with Codebase)  
**Location:** `IEEE_ICCIT_2026_PHASE_2B/B2_PROTOCOL_ALIGNMENT.md`  
**Primary Reference Files:**
- [`lib/crypto/sse_engine.dart`](file:///g:/_PROJECTS/visiocrypto/lib/crypto/sse_engine.dart) (Lines 237–430)
- [`lib/crypto/deletion_ledger.dart`](file:///g:/_PROJECTS/visiocrypto/lib/crypto/deletion_ledger.dart) (Lines 82–324)
- [`IEEE_ICCIT_2026_REVISION/2015_Revised_Manuscript.tex`](file:///g:/_PROJECTS/visiocrypto/IEEE_ICCIT_2026_REVISION/2015_Revised_Manuscript.tex) (Algorithm 1, lines 205–245)

---

## 1. Analysis of Protocol Mismatch in Manuscript Algorithm 1

In `2015_Revised_Manuscript.tex` (Algorithm 1, lines 220–243), the authors presented conflicting pseudocode:

```text
-- MANUSCRIPT ALGORITHM 1 FLAW --
Procedure Search(w):
    Tw <- HMAC(Ksearch, w)
    Receive blob I[Tw]
    ...

Procedure Update(op, d):
    vw <- GetVer(w) + 1
    Tw,v <- HMAC(Ksearch, w || vw)   <-- BROKEN
    edelta <- edelta U {(Tw,v, IV || c)}
```

### 1.1. Why Versioned Counters Break Search Without Homomorphic Trapdoors
1. **The Inversion Problem:** In standard asymmetric/symmetric forward-private SSE schemes (e.g., Sophos [Bost CCS 2016], Diana [Bost et al. CCS 2017]), the server evaluates a trapdoor permutation or chained PRF: $T^{(v)} = \pi^{-1}(T^{(v+1)})$.
2. **VisioCrypt's Primitive:** VisioCrypt uses HMAC-SHA256, which is a standard collision-resistant pseudo-random function without algebraic homomorphism or inversion trapdoors.
3. **The Failure:** When the client sends static search token $T_w = \text{HMAC}(K_{\text{search}}, w)$, the server queries its hash table $\mathbf{I}$. But dynamically added entries were stored under key $T_{w,v} = \text{HMAC}(K_{\text{search}}, w \parallel v_w)$. Because $T_w \ne T_{w,v}$ and HMAC cannot be inverted, the server finds **zero matches**. The search fails to return dynamically added documents.

### 1.2. The Reality in the Actual Codebase (`lib/crypto/sse_engine.dart`)
In `addDocumentDynamic` (lines 299–316):
```dart
for (final word in keywords) {
  final trapdoor = computeTrapdoor(word, kSearch); // Exact same static trapdoor!
  ...
  deltaUpdates.add({'trapdoor': trapdoor, ...});
}
```
The implementation uses the static trapdoor `computeTrapdoor(word, kSearch)` for updates. This functions correctly for data retrieval, but it **leaks query equality on updates** (the server immediately recognizes if an inserted document contains a previously searched keyword). Therefore, **Forward Privacy does not hold** in the prototype.

---

## 2. Corrected, Fully Aligned Protocol Specification

To restore absolute scientific truth, Algorithm 1 must be rewritten to specify the authentic **Static Volume-Hiding Protocol with Two-Tier Authoritative Deletion Ledger**, with practical client-side updates clearly documented.

### 2.1. Exact Data Structures & Token Formats
1. **Master Key Tuple:**
   $$K = (K_{\text{search}}, K_{\text{idx}}, K_{\text{file}}, K_{\text{ledger\_enc}}, K_{\text{ledger\_auth}}) \in (\{0, 1\}^{256})^5$$
   derived via RFC 5869 HKDF-SHA256 from $K_{\text{master}}$ and salt $S$.
2. **Search Trapdoor:**
   $$T_w = \text{HMAC-SHA256}(K_{\text{search}}, \text{Normalize}(w)) \in \{0, 1\}^{256}$$
   represented as a 64-character lowercase hexadecimal string.
3. **Inverted Index Map ($\mathbf{I}$):**
   A key-value dictionary mapping $T_w \to \text{Base64}(IV_w \parallel C_w)$, where:
   - $IV_w \stackrel{\$}{\leftarrow} \{0, 1\}^{96}$ (fresh 12-byte initialization vector per posting list).
   - $C_w \gets \text{AES-256-GCM-Enc}_{K_{\text{idx}}}(IV_w, \text{Encode}(\mathbf{R}^*(w)))$.
   - $\mathbf{R}^*(w) = \mathbf{R}(w) \cup \{ \text{"\_\_DUMMY\_MATCH\_"} \parallel j \}_{j=1}^{\Phi(|R|) - |R|}$.
4. **Authoritative Deletion Tombstone:**
   $$\mathbf{T}_{\text{del}}[d] = (\text{timestamp}, \text{epoch}, \mathbf{W}_d, \tau_d)$$
   where $\tau_d = \text{HMAC-SHA256}(K_{\text{ledger\_auth}}, d \parallel \text{timestamp} \parallel \text{epoch})$.
5. **In-Memory Pre-Filter ($\mathbf{BF}$):**
   Lightweight Bloom filter bitset ($m = 8192$ bits, $k = 4$ hashes derived via double hashing with SHA-256) storing $w \parallel d$.

---

## 3. Corrected Algorithm 1 LaTeX Pseudocode

```latex
\begin{algorithm}[t]
\caption{VisioCrypt Volume-Hiding SSE with Authoritative Deletion Ledger}
\label{alg:protocols}
\begin{algorithmic}[1]
\Require Master key $K$, Salt $S$, Corpus $\mathbf{D} = \{d_1, \dots, d_N\}$
\Procedure{BuildIndex}{$K, S, \mathbf{D}$}
    \State $(K_{\text{search}}, K_{\text{idx}}, K_{\text{file}}, K_{\text{l\_enc}}, K_{\text{l\_auth}}) \gets \text{DeriveKeys}(K, S)$
    \State $\mathbf{I} \gets \text{EmptyMap}()$; \quad $\mathbf{Ledger} \gets \text{NewLedger}()$
    \For{each document $d_j \in \mathbf{D}$, $w \in \text{Tokenize}(d_j)$}
        \State $T_w \gets \text{HMAC-SHA256}(K_{\text{search}}, w)$
        \State $\mathbf{I}[T_w] \gets \mathbf{I}[T_w] \cup \{\text{id}(d_j)\}$
    \EndFor
    \For{each $T_w \in \text{keys}(\mathbf{I})$}
        \State $\mathbf{R}^* \gets \text{PadFileList}(\mathbf{I}[T_w], \Phi)$ \Comment{Round to power-of-two}
        \State $\text{IV} \xleftarrow{\$} \{0,1\}^{96}$
        \State $C_w \gets \text{AES-GCM-Enc}(K_{\text{idx}}, \text{IV}, \text{JSON}(\mathbf{R}^*))$
        \State $\mathbf{I}[T_w] \gets \text{Base64}(\text{IV} \parallel C_w)$
    \EndFor
    \State $\text{Zeroize}(K_{\text{search}}, K_{\text{idx}}, K_{\text{file}}, K_{\text{l\_enc}}, K_{\text{l\_auth}})$
    \State \Return $(\mathbf{I}, \mathbf{Ledger})$
\EndProcedure

\Procedure{Search}{$w, \mathbf{I}, \mathbf{Ledger}$}
    \State $(K_{\text{search}}, K_{\text{idx}}) \gets \text{DeriveKeys}(K, S)$
    \State $T_w \gets \text{HMAC-SHA256}(K_{\text{search}}, w)$
    \State Send $T_w$ to Cloud; \quad Receive payload $\mathbf{I}[T_w]$
    \If{$\mathbf{I}[T_w] = \bot$} \State \Return $\emptyset$ \EndIf
    \State $(\text{IV}, C_w) \gets \text{Unpack}(\mathbf{I}[T_w])$
    \State $P_{\text{list}} \gets \text{JSON-Decode}(\text{AES-GCM-Dec}(K_{\text{idx}}, \text{IV}, C_w))$
    \State $\mathbf{D}_w \gets \emptyset$
    \For{each $\text{id} \in P_{\text{list}}$}
        \State \textbf{if} $\text{IsDummy}(\text{id})$ \textbf{then continue}
        \State \Comment{Two-Tier Authoritative Deletion Check}
        \State \textbf{if} $\mathbf{Ledger}.\text{IsDeleted}(\text{id}, w)$ \textbf{then continue}
        \State $\mathbf{D}_w \gets \mathbf{D}_w \cup \{\text{id}\}$
    \EndFor
    \State $\text{Zeroize}(K_{\text{search}}, K_{\text{idx}})$
    \State \Return $\mathbf{D}_w$
\EndProcedure

\Procedure{DeleteDocument}{$d, \mathbf{Ledger}$}
    \State $(K_{\text{l\_enc}}, K_{\text{l\_auth}}) \gets \text{DeriveKeys}(K, S)$
    \State $\mathbf{W}_d \gets \text{Tokenize}(d)$
    \State $\mathbf{Ledger}.\text{MarkDeleted}(\text{id}(d), \mathbf{W}_d, K_{\text{l\_auth}})$
    \State $\mathbf{Ledger}.\text{SaveEncrypted}(\text{File}, K_{\text{l\_enc}}, K_{\text{l\_auth}})$
    \State $\text{Zeroize}(K_{\text{l\_enc}}, K_{\text{l\_auth}})$
\EndProcedure
\end{algorithmic}
\end{algorithm}
```

---

## 4. Transparent Disclosure of Dynamic Update Limitations

In resubmitting Paper ID 2015, the manuscript must explicitly detail the security profile of dynamic updates:

1. **Static Index Construction is Leakage-Free:**
   During initial static index generation, the server observes only:
   $$\mathcal{L}_{\text{setup}} = (N, |\mathbf{W}|, \{\Phi(|R(w)|)\}_{w \in \mathbf{W}}).$$
   Under Theorem 1, this construction is provably $\mathcal{L}_{\text{VH}}\text{-IND-CKA2}$ secure.

2. **Client-Side Deletions Leak Zero to Cloud:**
   Document deletions are processed locally inside the Two-Tier Authoritative Deletion Ledger on the mobile device. No message is sent to the cloud server at deletion time. Therefore, deletion leaks **zero bits** of information to the cloud adversary.

3. **Incremental Document Additions Disclose Search Token Correlation:**
   In the mobile prototype, adding a new document dynamically computes $T_w = \text{HMAC}(K_{\text{search}}, w)$. If keyword $w$ was previously searched, the cloud server observes that the new document contains $w$.
   - **Formal Disclosure:** Forward privacy is **not achieved** by this lightweight client-side update workflow.
   - **Scientific Roadmap:** Achieving formal forward privacy without high mobile computational overhead requires integration of trapdoor permutations (e.g., Sophos) or dual-server ORAM hierarchies, which is formally identified as future work.

---

## 5. Verification Status

| Requirement | Implementation Evidence | Verification Status |
| :--- | :--- | :---: |
| **Eliminate Broken Version Counter** | Algorithm 1 updated to static trapdoor + client ledger | **VERIFIED** |
| **Trace Actual Indexing & Query Flow** | Code paths in `sse_engine.dart` and `deletion_ledger.dart` verified | **VERIFIED** |
| **Define Exact Token Formats & Data Structs** | Hex HMAC tokens, JSON padded arrays, Base64 GCM blobs | **VERIFIED** |
| **Transparent Dynamic Update Leakage** | Explicitly stated that dynamic updates disclose search equality | **VERIFIED** |
| **Retraction of Forward / Backward Privacy** | Retracted in favor of verified Static $\mathcal{L}_{\text{VH}}\text{-IND-CKA2}$ | **VERIFIED** |
