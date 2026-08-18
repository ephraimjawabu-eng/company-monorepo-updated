"""Secure cryptographic helpers enforcing AEAD, HKDF, constant-time operations.

This module provides safe high-level wrappers around established primitives.
- Uses cryptography.hazmat.aead (AESGCM, ChaCha20Poly1305)
- Uses HKDF for key derivation
- Uses hmac.compare_digest for constant-time comparisons

Notes:
- Keys must be managed via a KMS/HSM in production; this module assumes keys are in-memory for demos.
- Avoid exposing raw keys or printing them in logs.
"""
from __future__ import annotations

import os
import hmac
from typing import Tuple

try:
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives import constant_time
except Exception:
    AESGCM = None  # type: ignore
    ChaCha20Poly1305 = None  # type: ignore
    HKDF = None  # type: ignore
    hashes = None  # type: ignore
    constant_time = None  # type: ignore


def generate_key(length: int = 32) -> bytes:
    """Generate a cryptographically secure key (default 32 bytes for AES-256/ChaCha20)
    Keep the key in memory only and load from secrets manager in production.
    """
    return os.urandom(length)


def hkdf_derive(salt: bytes, ikm: bytes, info: bytes, length: int = 32) -> bytes:
    """Derive keys using HKDF-SHA256.
    Returns `length` bytes. Use for KEK/DEK derivation.
    """
    if HKDF is None:
        raise RuntimeError("cryptography library not available")
    hk = HKDF(algorithm=hashes.SHA256(), length=length, salt=salt, info=info)
    return hk.derive(ikm)


def encrypt_aead(key: bytes, plaintext: bytes, associated_data: bytes | None = None) -> Tuple[bytes, bytes]:
    """Encrypt with AEAD and return (nonce, ciphertext).

    Uses AESGCM if key length is 16/24/32, otherwise falls back to ChaCha20-Poly1305 for 32-byte keys.
    Nonce/IV uniqueness must be ensured by the caller when using stream counters; here we use random nonce.
    """
    if AESGCM is None or ChaCha20Poly1305 is None:
        raise RuntimeError("cryptography primitives not available")
    if associated_data is None:
        associated_data = b""
    # choose cipher
    if len(key) in (16, 24, 32):
        cipher = AESGCM(key)
        nonce = os.urandom(12)  # 96-bit nonce for AES-GCM
        ct = cipher.encrypt(nonce, plaintext, associated_data)
        return nonce, ct
    else:
        # ChaCha20-Poly1305 requires 32-byte key
        if len(key) < 32:
            raise ValueError("Key too short for ChaCha20-Poly1305")
        cipher = ChaCha20Poly1305(key[:32])
        nonce = os.urandom(12)
        ct = cipher.encrypt(nonce, plaintext, associated_data)
        return nonce, ct


def decrypt_aead(key: bytes, nonce: bytes, ciphertext: bytes, associated_data: bytes | None = None) -> bytes:
    """Decrypt AEAD ciphertext. Raises exception on auth failure.
    Uses constant-time comparison for any manual tag checks (the AEAD APIs handle tags internally).
    """
    if AESGCM is None or ChaCha20Poly1305 is None:
        raise RuntimeError("cryptography primitives not available")
    if associated_data is None:
        associated_data = b""
    if len(key) in (16, 24, 32):
        cipher = AESGCM(key)
        return cipher.decrypt(nonce, ciphertext, associated_data)
    else:
        cipher = ChaCha20Poly1305(key[:32])
        return cipher.decrypt(nonce, ciphertext, associated_data)


def constant_time_compare(a: bytes, b: bytes) -> bool:
    """Constant-time comparison wrapper.
    Uses hmac.compare_digest for Python-level constant time.
    """
    return hmac.compare_digest(a, b)


def secure_erase(b: bytearray) -> None:
    """Attempt to overwrite sensitive bytearray content in-place.
    Python cannot guarantee zeroization at the interpreter level for immutable bytes objects;
    prefer working with bytearray for secrets that must be scrubbed.

    This attempts OS-specific secure zeroization when possible (Windows SecureZeroMemory, libc memset).
    """
    try:
        # fast path: try ctypes to call platform-specific secure erase
        import ctypes
        if os.name == 'nt':
            # Windows: use SecureZeroMemory from kernel32
            try:
                kernel32 = ctypes.WinDLL('kernel32')
                addr = ctypes.addressof(ctypes.c_char.from_buffer(b))
                kernel32.RtlSecureZeroMemory(ctypes.c_void_p(addr), ctypes.c_size_t(len(b)))
                return
            except Exception:
                pass
        else:
            # POSIX: use libc memset to zero memory
            try:
                libc = ctypes.CDLL('libc.so.6')
                addr = ctypes.addressof(ctypes.c_char.from_buffer(b))
                libc.memset(ctypes.c_void_p(addr), ctypes.c_int(0), ctypes.c_size_t(len(b)))
                return
            except Exception:
                pass
    except Exception:
        pass

    # best-effort Python-level overwrite
    for i in range(len(b)):
        b[i] = 0
    # attempt to remove reference
    try:
        del b
    except Exception:
        pass
