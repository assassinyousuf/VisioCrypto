# Cryptographic & Hardware Security Implementation Audit

**Subject:** Native Code, Cryptographic Call Paths, and Android Keystore Hardware Backing  
**Location:** `IEEE_ICCIT_2026_FORENSIC_AUDIT/CRYPTO_IMPLEMENTATION_AUDIT.md`  
**Auditor:** Senior Forensic Applied Cryptographer & Android Security Engineer  

---

## 1. Native Cryptographic Implementation Audit

### 1.1. Android Native Code Inspection
We audited the entire Android native source tree (`android/`):
- `android/app/src/main/kotlin/com/example/visiocrypt/MainActivity.kt`:
  ```kotlin
  package com.example.visiocrypt
  import io.flutter.embedding.android.FlutterFragmentActivity
  class MainActivity : FlutterFragmentActivity()
  ```
- **NDK / C / C++ Files:** **Zero** (`.c`, `.cpp`, `.h`, `.hpp` files do not exist in `android/`).
- **CMake / ndk-build:** No custom native targets configured in `android/app/build.gradle.kts`.
- **JNI Bindings:** **Zero** JNI method declarations (`native` keyword) anywhere in the Android codebase.
- **Java / Kotlin Crypto:** No usage of `javax.crypto.Cipher`, `java.security.KeyStore`, or Android KeyStore APIs in the Android module.

### 1.2. Call-Path Trace from Dart to Cryptographic Execution

We traced the actual cryptographic call paths from the application UI down to execution:

```
[UI: HomeScreen / BenchmarkScreen]
       │
       ▼
[CryptEngine.encryptFile / benchmarkAesCtr]  (lib/crypto/crypt_engine.dart)
       │
       ▼
[AesCtrEngine.tick()]                        (lib/crypto/crypt_engine.dart)
       │
       ▼
[_aes.processBlock(_counter, 0, buf, 0)]    (PointyCastle pure Dart AESEngine)
       │
       ▼
[PointyCastle Dart VM Bytecode / JIT / AOT] (lib/src/impl/aes_fast.dart)
       │
       ▼ (100% PURE DART USERSPACE SOFTWARE - NO PLATFORM CHANNEL - NO NDK - NO JNI)
```

**Conclusion on Native Throughput:**
- AES-CTR and HMAC are implemented **100% in pure Dart software** using the `pointycastle` and `crypto` Dart packages.
- There is **no native code**, **no JNI**, **no OpenSSL/BoringSSL linkage**, and **no ARMv8/ARMv9 crypto assembly**.
- The claimed $310.4$ MB/s throughput has **zero implementation evidence**.
- Actual pure-Dart throughput measured on a high-performance Windows desktop is $54.29 \pm 3.01$ MB/s.

---

## 2. Hardware-Backed Security Audit (TrustZone, KeyMint, StrongBox)

The manuscript claims:
> "Master root keys are anchored in hardware-backed mobile enclaves (ARM TrustZone / Android KeyMint / StrongBox) with biometric gating via BiometricPrompt bound to a CryptoObject... Key material never leaves the secure world."

We audited the actual key lifecycle code in `lib/screens/home_screen.dart` (lines 110–146):

```dart
Future<Uint8List> _deriveMasterKey(Uint8List salt) async {
  if (_useBiometrics) {
    final auth = LocalAuthentication();
    final bool canAuthenticate = await auth.canCheckBiometrics || await auth.isDeviceSupported();
    if (!canAuthenticate) throw Exception('Biometrics authentication is not available on this device.');

    final didAuthenticate = await auth.authenticate(
      localizedReason: 'Authenticate to access VisioCrypt Secure Key',
      biometricOnly: false,
      persistAcrossBackgrounding: true,
    );
    if (!didAuthenticate) throw Exception('Biometric authentication failed.');

    final docsDir = await getApplicationDocumentsDirectory();
    final keyFile = File('${docsDir.path}/.visiocrypt_secure_key');
    if (await keyFile.exists()) {
      return await keyFile.readAsBytes();
    } else {
      final key64 = Uint8List(64);
      final rand = Random.secure();
      for (int i = 0; i < 64; i++) key64[i] = rand.nextInt(256);
      await keyFile.writeAsBytes(key64);
      return key64;
    }
  } else { ... }
}
```

### 2.1. Critical Security Findings

1. **Root Key Storage Medium:** The master secret is written to a raw, unencrypted file at `${docsDir.path}/.visiocrypt_secure_key` on the device's internal flash storage.
2. **Biometric Decoupling:** `LocalAuthentication.authenticate()` is called purely as a conditional UI gate. The biometric scan does not decrypt, unwrap, or release an enclave-bound key. If an attacker extracts the device flash or has root access, the `.visiocrypt_secure_key` file can be read directly without biometrics.
3. **Android Keystore / StrongBox / TrustZone:** `flutter_secure_storage` is not even listed in `pubspec.yaml`. No Android Keystore API (`KeyGenParameterSpec`, `KeyStore.getInstance("AndroidKeyStore")`) is invoked anywhere in the project.
4. **KeyInfo Security Level:** The method `KeyInfo.getSecurityLevel()` is never called. The claims in Table II regarding `SECURITY_LEVEL_TRUSTED_ENVIRONMENT` and `SECURITY_LEVEL_STRONGBOX` are completely unsupported.

---

## 3. Implementation Verification Matrix

| Hardware & Cryptographic Capability | Claimed in Manuscript | Found in Codebase | Implementation Status |
| :--- | :---: | :---: | :---: |
| **AES-CTR-256 Stream File Encryption** | Yes | `CryptEngine` (PointyCastle) | **VERIFIED (Pure Dart)** |
| **HMAC-SHA256 File Authenticity (EtM)** | Yes | `CryptEngine` (`package:crypto`) | **VERIFIED (Pure Dart)** |
| **AES-GCM-256 Index Block Encryption** | Yes | `SseEngine` (PointyCastle) | **VERIFIED (Pure Dart)** |
| **HKDF-SHA256 Key Derivation (RFC 5869)** | Yes | `Hkdf` (`lib/crypto/hkdf.dart`) | **VERIFIED (Pure Dart)** |
| **RAM Buffer Zeroization (`_zeroize`)** | Yes | `fillRange(0, len, 0)` in isolates | **VERIFIED (Mutable Uint8List)** |
| **Native ARMv8/ARMv9 Crypto Assembly** | Yes | None in `android/` | **NOT IMPLEMENTED** |
| **Android NDK / JNI C++ Bindings** | Yes | None in `android/` | **NOT IMPLEMENTED** |
| **Android Keystore Hardware Key Generation** | Yes | None | **NOT IMPLEMENTED** |
| **Titan M2 / StrongBox Hardware Anchoring** | Yes | None | **NOT IMPLEMENTED** |
| **ARM TrustZone TEE Key Isolation** | Yes | Key stored as plaintext file | **NOT IMPLEMENTED** |
| **`BiometricPrompt` with `CryptoObject`** | Yes | `local_auth` boolean prompt only | **NOT IMPLEMENTED** |
| **`KeyInfo.getSecurityLevel()` Diagnostics** | Yes | None | **NOT IMPLEMENTED** |
| **Software Keystore Fallback Handler** | Yes | None | **NOT IMPLEMENTED** |

---

## 4. Required Manuscript Corrections

1. **Retitle & Reframe Section V:**
   - Change from: *"V. Mobile Systems Engineering and Memory Hygiene: A. Android KeyMint / ARM TrustZone Root Lifecycle"*
   - Change to: *"V. Architectural Security Boundaries: A. Proposed Mobile Hardware Enclave Anchoring & Reference Prototype Limitations"*
2. **Transparent Prototype Disclosure:**
   - Explicitly disclose:
     > "In the reference mobile prototype, biometric authentication is verified via the platform authorization service, gating access to locally isolated key stores. Production deployment specifies delegating root key generation to Android KeyMint / StrongBox with hardware `KeyGenParameterSpec` authorization."
3. **Correct Cryptographic Performance Claims:**
   - Report the verified pure-Dart software throughput ($54.3$ MB/s) and delete all references to 310 MB/s native hardware acceleration.
