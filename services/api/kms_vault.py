"""Example Vault KMS integration helper (non-functional placeholder).

This file demonstrates how to wire HashiCorp Vault requests for retrieving a KEK.
DO NOT commit credentials. Use environment-based auth methods (AWS/IAM, AppRole, GCP) in production.

The implementation intentionally uses a minimal requests-based approach. In production, prefer
an official Vault client library and mTLS or cloud auth methods.
"""
from __future__ import annotations

import os
import logging
from typing import Optional

import requests

log = logging.getLogger("kms_vault")


class VaultKMS:
    def __init__(self, base_url: Optional[str] = None, token: Optional[str] = None) -> None:
        self.base_url = base_url or os.environ.get('VAULT_ADDR')
        self.token = token or os.environ.get('VAULT_TOKEN')

    def _headers(self) -> dict:
        h = {'Content-Type': 'application/json'}
        if self.token:
            h['Authorization'] = f'Bearer {self.token}'
        return h

    def get_secret_bytes(self, path: str, key: str = 'value') -> Optional[bytes]:
        if not self.base_url or not self.token:
            log.warning('Vault credentials not configured; cannot fetch secret')
            return None
        url = f"{self.base_url}/v1/{path}"
        try:
            r = requests.get(url, headers=self._headers(), timeout=5.0)
            r.raise_for_status()
            j = r.json()
            # Vault kv v2 stores under data.data
            val = j.get('data', {}).get('data', {}).get(key)
            if val is None:
                return None
            if isinstance(val, str):
                return val.encode('utf-8')
            if isinstance(val, bytes):
                return val
            return str(val).encode('utf-8')
        except Exception:
            log.exception('Failed to fetch secret from Vault')
            return None


# Example helper that fetches KEK bytes from Vault and returns them
def fetch_kek_from_vault(secret_path: str = 'secret/data/keystore/master_kek') -> Optional[bytes]:
    client = VaultKMS()
    return client.get_secret_bytes(secret_path, key='kek')
