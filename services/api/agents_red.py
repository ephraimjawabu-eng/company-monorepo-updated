"""Red team agents: reconnaissance and cryptanalysis simulators.
"""
from __future__ import annotations
from typing import Any, Dict, List

from services.api.topology import GraphTopology


class GraphReconAgent:
    def __init__(self, topology: GraphTopology):
        self.topology = topology

    def discover(self) -> Dict[str, Any]:
        nodes = list(self.topology.nodes())
        sensitive = self.topology.sensitive_assets()
        central = self.topology.centrality_ranking(k=5)
        return {
            'nodes_count': len(nodes),
            'sensitive': sensitive,
            'central_nodes': central,
        }


class CryptanalysisAgent:
    def __init__(self):
        pass

    def audit_crypto_wrappers(self) -> List[Dict[str, str]]:
        """Naive static checks: ensure crypto helpers exist and AEAD used.
        In production this should run binary/provenance checks and constant-time validators.
        """
        findings: List[Dict[str, str]] = []
        try:
            from services.api import crypto
            # presence check
            if not hasattr(crypto, 'encrypt_aead'):
                findings.append({'issue': 'missing_aead', 'detail': 'encrypt_aead not found'})
            else:
                findings.append({'issue': 'ok', 'detail': 'aead_present'})
        except Exception as e:
            findings.append({'issue': 'crypto_import_failed', 'detail': str(e)})
        return findings
