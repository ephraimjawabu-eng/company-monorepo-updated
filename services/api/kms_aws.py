"""AWS KMS helper (placeholder).

Uses boto3 to encrypt/decrypt or generate data keys via AWS KMS. This module is a safe, minimal wrapper
that the production code can call. It intentionally does not embed any credentials and relies on standard
AWS SDK credential loading (env, profile, IAM role).

Functions:
- generate_data_key(kms_key_id, key_spec='AES_256') -> (plaintext, ciphertext)
- decrypt_data_key(ciphertext) -> plaintext

Note: boto3 must be installed and AWS credentials configured for real usage.
"""
from __future__ import annotations

import logging
from typing import Optional, Tuple

try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None  # type: ignore

log = logging.getLogger("kms_aws")


def generate_data_key(kms_key_id: str, key_spec: str = 'AES_256') -> Optional[Tuple[bytes, bytes]]:
    """Generate a data key using AWS KMS. Returns (plaintext_bytes, ciphertext_blob).

    Caller should immediately zero the plaintext bytes after wrapping the DEK in a KEK.
    """
    if boto3 is None:
        log.error('boto3 not available')
        return None
    try:
        client = boto3.client('kms')
        resp = client.generate_data_key(KeyId=kms_key_id, KeySpec=key_spec)
        return resp.get('Plaintext'), resp.get('CiphertextBlob')
    except (BotoCoreError, ClientError):
        log.exception('KMS generate_data_key failed')
        return None


def decrypt_data_key(ciphertext_blob: bytes) -> Optional[bytes]:
    if boto3 is None:
        log.error('boto3 not available')
        return None
    try:
        client = boto3.client('kms')
        resp = client.decrypt(CiphertextBlob=ciphertext_blob)
        return resp.get('Plaintext')
    except (BotoCoreError, ClientError):
        log.exception('KMS decrypt failed')
        return None
