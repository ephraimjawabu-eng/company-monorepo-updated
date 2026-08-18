"""KMS stub / helper for secure key retrieval and derivation.

This module provides a minimal interface that production code can swap out for real Vault/KMS/HSM integrations.
It intentionally avoids any hard-coded secrets and demonstrates HKDF-based DEK derivation from a KEK.

Notes:
- For demo environments, set KMS_BACKEND=env and provide KEK_BASE64 in env (base64-encoded raw bytes).
- In production, implement a backend for Vault/AWS KMS and prefer hardware-backed keys.
"""
from __future__ import annotations

import os
import base64
import logging
from typing import Optional

from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives import hashes

log = logging.getLogger("kms")


class KMSClient:
    """Minimal KMS client abstraction.

    Usage:
      client = KMSClient()
      kek = client.get_kek()  # raw bytes
      dek = client.derive_dek(kek, context=b"service:storage")

    Backends supported (demo):
      - env: reads KEK_BASE64 from environment
      - keyring: reads API key or KEK from OS keyring via python-keyring (user-level)

    In production, replace with Vault/AWS KMS/HSM implementations.
    """

    def __init__(self) -> None:
        self.backend = os.environ.get("KMS_BACKEND", "env")

    def get_kek(self) -> Optional[bytes]:
        """Retrieve the master KEK as raw bytes.

        For demo: read KEK_BASE64 from environment. If backend == 'keyring', attempt to read
        a stored entry named 'company_engine_kek' from the OS keyring (python-keyring).
        """
        if self.backend == "env":
            b64 = os.environ.get("KEK_BASE64")
            if not b64:
                log.warning("KEK_BASE64 not set in env; KEK unavailable")
                return None
            try:
                return base64.b64decode(b64)
            except Exception:
                log.exception("Failed to decode KEK_BASE64")
                return None
        if self.backend == "keyring":
            try:
                import keyring
                val = keyring.get_password('company_engine', 'master_kek')
                if not val:
                    log.warning('No master_kek found in keyring')
                    return None
                # expect base64-encoded stored value
                return base64.b64decode(val)
            except Exception:
                log.exception('Failed to read KEK from keyring')
                return None
        # TODO: add hooks for Vault, AWS KMS, GCP KMS, HSM, etc.
        log.error("Unsupported KMS_BACKEND: %s", self.backend)
        return None

    def derive_dek(self, kek: bytes, context: bytes = b"") -> bytes:
        """Derive a per-use Data Encryption Key (DEK) from the KEK using HKDF-SHA256.

        Returns raw bytes suitable for passing to AEAD primitives (truncate/expand as needed by algorithm).
        """
        if not kek:
            raise ValueError("KEK is required")
        hk = HKDF(algorithm=hashes.SHA256(), length=32, salt=None, info=context)
        return hk.derive(kek)


kms_client = KMSClient()


def get_dek_for_context(context: str | bytes) -> Optional[bytes]:
    ctx = context if isinstance(context, bytes) else context.encode("utf-8")
    kek = kms_client.get_kek()
    if kek is None:
        return None
    return kms_client.derive_dek(kek, context=ctx)
