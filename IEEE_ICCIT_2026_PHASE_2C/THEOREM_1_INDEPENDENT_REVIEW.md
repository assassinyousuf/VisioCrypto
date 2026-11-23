# Phase 2C Deliverable 3: Independent Review of Theorem 1 & Security Proof

**Subject:** Independent Reconstruction and Audit of Static Volume-Hiding Security Proof (Theorem 1)  
**Status:** **APPROVED WITH EXPLICIT SCOPING**  
**Location:** `IEEE_ICCIT_2026_PHASE_2C/THEOREM_1_INDEPENDENT_REVIEW.md`  
**Primary Reference:**
- [`IEEE_ICCIT_2026_AUDIT_CORRECTIONS/STATIC_SECURITY_PROOF_REASSESSMENT.md`](file:///g:/_PROJECTS/visiocrypto/IEEE_ICCIT_2026_AUDIT_CORRECTIONS/STATIC_SECURITY_PROOF_REASSESSMENT.md)
- [`IEEE_ICCIT_2026_REVISION/2015_Revised_Manuscript.tex`](file:///g:/_PROJECTS/visiocrypto/IEEE_ICCIT_2026_REVISION/2015_Revised_Manuscript.tex) (Section VI, lines 285–305)

---

## 1. Executive Summary

In Section VI of `2015_Revised_Manuscript.tex`, the authors presented Theorem 1 claiming adaptive security under a dynamic volume-hiding leakage function $\mathcal{L}_{\text{dyn-VH}}$.

**Independent Audit Finding:**
1. The dynamic security claim was **flawed and unsupportable** because the prototype's dynamic update routine computes static trapdoors $T_w = \text{HMAC}(K_{\text{search}}, w)$, leaking keyword search equality across updates and violating Forward Privacy.
2. However, for the **Static VisioCrypt Protocol**, the mathematical reduction from adaptive indistinguishability ($\mathcal{L}_{\text{VH}}\text{-IND-CKA2}$) to the underlying standard primitives (HKDF, HMAC-SHA256, and AES-256-GCM) is **sound, complete, and provably watertight**.

This review independently reconstructs the security game, validates the leakage profile, verifies simulator distribution equivalence, and establishes the strict boundaries within which Theorem 1 is publication-grade.

---

## 2. Security Model & Adversarial Game Definition

We reconstruct the standard adaptive chosen-keyword attack security game ($\text{IND-CKA2}$) for static searchable symmetric encryption (Curtmola et al., CCS 2006).

### 2.1. Adversary Capabilities
- Let $\mathcal{A}$ be a stateful Probabilistic Polynomial-Time (PPT) adversary.
- The adversary operates in the adaptive setting: queries are chosen sequentially, with each query $w_t$ chosen adaptively based on the complete history of previous transcripts, stored index structures, and candidate payload lengths.

### 2.2. The $\text{Real}_{\Sigma, \mathcal{A}}(\lambda)$ Experiment
1. $\mathcal{A}(1^\lambda)$ chooses a document collection $\mathbf{D}$.
2. The challenger runs $K \gets \text{KeyGen}(1^\lambda)$ and $\mathbf{I} \gets \text{BuildIndex}(K, \mathbf{D})$.
3. The challenger gives $\mathbf{I}$ to $\mathcal{A}$.
4. $\mathcal{A}$ adaptively issues a polynomial number of search queries $w_1, \dots, w_q$. For each query, the challenger computes $T_{w_t} \gets \text{Trapdoor}(K, w_t)$ and sends $T_{w_t}$ to $\mathcal{A}$.
5. $\mathcal{A}$ outputs a bit $b \in \{0, 1\}$.

### 2.3. The $\text{Ideal}_{\Sigma, \mathcal{S}, \mathcal{A}}(\lambda)$ Experiment
1. $\mathcal{A}(1^\lambda)$ chooses $\mathbf{D}$.
2. The challenger provides setup leakage $\mathcal{L}_{\text{setup}}(\mathbf{D})$ to the ideal simulator $\mathcal{S}$.
3. $\mathcal{S}(\mathcal{L}_{\text{setup}})$ outputs a simulated index $\mathbf{I}^*$, which is given to $\mathcal{A}$.
4. For each adaptive query $w_t$, the challenger provides query leakage $\mathcal{L}_{\text{search}}(w_t)$ to $\mathcal{S}$.
5. $\mathcal{S}(\mathcal{L}_{\text{search}})$ generates simulated trapdoor $\tilde{T}_{w_t}$, which is given to $\mathcal{A}$.
6. $\mathcal{A}$ outputs a bit $b \in \{0, 1\}$.

### 2.4. Definition of Adaptive Security
The static scheme $\Sigma$ is adaptively secure under leakage function $\mathcal{L}_{\text{VH}}$ if for every PPT adversary $\mathcal{A}$, there exists a PPT simulator $\mathcal{S}$ such that:
$$\mathbf{Adv}_{\Sigma, \mathcal{S}, \mathcal{A}}^{\mathcal{L}_{\text{VH}}\text{-IND-CKA2}}(\lambda) = \left| \Pr[\text{Real}_{\Sigma, \mathcal{A}}(\lambda) = 1] - \Pr[\text{Ideal}_{\Sigma, \mathcal{S}, \mathcal{A}}(\lambda) = 1] \right| \le \text{negl}(\lambda).$$

---

## 3. Leakage Function Completeness Audit

The static volume-hiding leakage function is formalized as:
$$\mathcal{L}_{\text{VH}}(\mathbf{D}, \mathbf{q}) = (\mathcal{L}_{\text{setup}}(\mathbf{D}), \mathcal{L}_{\text{search}}(w_1), \dots, \mathcal{L}_{\text{search}}(w_q)).$$

### 3.1. Setup Leakage
$$\mathcal{L}_{\text{setup}}(\mathbf{D}) = \left( N, |\mathbf{W}|, \{ \Phi(|R(w)|) \}_{w \in \mathbf{W}} \right)$$
- $N = |\mathbf{D}|$: Total document count.
- $|\mathbf{W}|$: Total unique keyword vocabulary size.
- $\{ \Phi(|R(w)|) \}$: The multiset of power-of-two padded posting list sizes:
  $$\Phi(n) = \begin{cases} 4 & \text{if } n \le 4 \\ 2^{\lceil \log_2 n \rceil} & \text{if } 4 < n \le 4096 \\ \lceil n / 4096 \rceil \cdot 4096 & \text{if } n > 4096 \end{cases}$$
- **Completeness Check:** Because the server stores $|\mathbf{W}|$ ciphertext blobs whose byte lengths are $L(\Phi(|R(w)|)) = 12 + \text{Len}(\text{JSON}) + 16$, the adversary directly observes the multiset of ciphertext lengths. The leakage function captures exactly what the server observes—nothing less, nothing more.

### 3.2. Search Leakage
$$\mathcal{L}_{\text{search}}(w_t) = \left( sp(w_t), ap(w_t), \Phi(|R(w_t)|) \right)$$
- $sp(w_t) = \{ j \le t \mid w_j = w_t \}$: Query equality pattern.
- $ap(w_t) = \{ \text{id}(d) \mid d \in \mathbf{D}, w_t \in \mathbf{W}_d \}$: Matching document access pattern.
- $\Phi(|R(w_t)|)$: Padded candidate size returned to client.
- **Completeness Check:** Since trapdoors $T_w = \text{HMAC}(K_{\text{search}}, w)$ are deterministic, repeat queries produce identical tokens ($sp(w_t)$). The server observes which index entry is accessed ($ap(w_t)$) and its bucket length $\Phi(|R(w_t)|)$.

---

## 4. Simulator Construction & Equivalence Verification

We independently audit the simulator $\mathcal{S} = (\mathcal{S}_{\text{setup}}, \mathcal{S}_{\text{search}})$:

### 4.1. Simulator Construction
1. **$\mathcal{S}_{\text{setup}}(\mathcal{L}_{\text{setup}})$:**
   - On input $(N, |\mathbf{W}|, \{ M_i \}_{i=1}^{|\mathbf{W}|})$:
   - For $i = 1$ to $|\mathbf{W}|$:
     - Sample $\tilde{T}_i \stackrel{\$}{\leftarrow} \{0, 1\}^{256}$.
     - Sample $IV_i \stackrel{\$}{\leftarrow} \{0, 1\}^{96}$.
     - Encrypt a string of all-zero bytes of identical length:
       $$\tilde{C}_i \gets \text{AES-GCM-Enc}_{\tilde{K}}(IV_i, 0^{L(M_i)}).$$
     - Store $(\tilde{T}_i, \text{Base64}(IV_i \parallel \tilde{C}_i))$ into simulated index $\mathbf{I}^*$.
   - Return $\mathbf{I}^*$.
2. **$\mathcal{S}_{\text{search}}(\mathcal{L}_{\text{search}}(w_t))$:**
   - On input $(sp(w_t), ap(w_t), M_t)$:
   - Check if $w_t$ was previously queried ($j = \min(sp(w_t)) < t$):
     - If yes: return previously assigned trapdoor $\tilde{T}_j$.
     - If no (fresh query):
       - Sample fresh uniform token $\tilde{T}_{w_t} \stackrel{\$}{\leftarrow} \{0, 1\}^{256}$.
       - Map an index entry with padded size $M_t$ to $\tilde{T}_{w_t}$.
       - Return $\tilde{T}_{w_t}$.

### 4.2. Distribution Equivalence Verification
- **Index Structure:** In the real scheme, $\mathbf{I}$ contains $|\mathbf{W}|$ tuples with pseudo-random keys and AES-GCM ciphertexts. In the ideal experiment, $\mathbf{I}^*$ contains $|\mathbf{W}|$ tuples with uniform keys and AES-GCM encryptions of zeros of identical length $L(M_i)$.
- **Search Tokens:** Real tokens are evaluations of HMAC-SHA256 under secret key $K_{\text{search}}$. Ideal tokens are uniform random strings with identical equality structure ($sp(w)$).
- **Indistinguishability:** Any PPT algorithm distinguishing $\mathbf{I}$ from $\mathbf{I}^*$ or $T_w$ from $\tilde{T}_w$ directly breaks the PRF security of HKDF, PRF security of HMAC, or IND-CPA security of AES-GCM.

---

## 5. Game Hopping Reductions Audit

We verify each game transition in the proof:

1. **Game 0 $\to$ Game 1 (HKDF PRF Replacement):**
   - Keys $(K_{\text{search}}, K_{\text{idx}})$ are replaced with uniform random keys.
   - Reduction: Bounded by $\mathbf{Adv}_{\text{HKDF}}^{\text{prf}}(\lambda)$. (Sound).
2. **Game 1 $\to$ Game 2 (HMAC PRF Replacement):**
   - Deterministic HMAC trapdoors are replaced with random function evaluations conditioned on $sp(w)$.
   - Reduction: Bounded by $\mathbf{Adv}_{\text{HMAC}}^{\text{prf}}(\lambda)$. (Sound).
3. **Game 2 $\to$ Game 3 (AES-GCM IND-CPA Replacement):**
   - Ciphertexts of padded candidate lists are replaced with ciphertexts of zero bytes of identical length $L(\Phi(|R|))$.
   - Reduction: Nonce uniqueness holds by sampling 96-bit random IVs ($P_{\text{IV-collision}} \le |\mathbf{W}|^2 / 2^{97} \le \text{negl}(\lambda)$). Bounded by $\mathbf{Adv}_{\text{AES-GCM}}^{\text{ind-cpa}}(\lambda)$. (Sound).
4. **Game 3 $\to$ Game 4 (Simulation by $\mathcal{S}$):**
   - The view in Game 3 uses only $(sp(w), ap(w), \Phi(|R(w)|))$, which matches the exact output of simulator $\mathcal{S}$.
   - Advantage: Exactly 0.

### Mathematical Total Bound:
$$\mathbf{Adv}_{\Sigma, \mathcal{S}, \mathcal{A}}^{\mathcal{L}_{\text{VH}}\text{-IND-CKA2}}(\lambda) \le \mathbf{Adv}_{\text{HKDF}}^{\text{prf}}(\lambda) + \mathbf{Adv}_{\text{HMAC}}^{\text{prf}}(\lambda) + \mathbf{Adv}_{\text{AES-GCM}}^{\text{ind-cpa}}(\lambda) + \frac{|\mathbf{W}|^2}{2^{97}} \le \text{negl}(\lambda).$$

---

## 6. Critical Proof Boundary: Static vs. Dynamic Updates

> [!CAUTION]
> **Defensibility Rule:** Theorem 1 is valid **ONLY** for the static scheme.
> - If dynamic updates are performed, inserting documents under $T_w = \text{HMAC}(K_{\text{search}}, w)$ violates the simulation because the simulator cannot know future update correlations without adding update history to the leakage function.
> - The manuscript must explicitly title Theorem 1 as:
>   **"Theorem 1 (Adaptive Security of Static Volume-Hiding Scheme)"**
> - Dynamic updates must be presented as an unproven client-side operational feature with transparently acknowledged search-equality leakage.

---

## 7. Final Audit Verdict

**APPROVED WITH EXPLICIT SCOPING.** The proof of Theorem 1 for Static Volume-Hiding VisioCrypt is mathematically sound, complete, and publication-ready. The manuscript must restrict the formal theorem statement strictly to the static protocol.
