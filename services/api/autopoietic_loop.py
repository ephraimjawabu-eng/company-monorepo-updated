"""Orchestrator: runs red and blue agents in a closed loop and logs outcomes.
"""
from __future__ import annotations
import time
from typing import Any

from services.api.topology import GraphTopology
from services.api.agents_red import GraphReconAgent, CryptanalysisAgent
from services.api.agents_blue import AutopoieticHardenerAgent


class AutopoieticLoop:
    def __init__(self, topology: GraphTopology, logger=None):
        self.topology = topology
        self.red_recon = GraphReconAgent(topology)
        self.crypto = CryptanalysisAgent()
        self.blue = AutopoieticHardenerAgent(topology)
        self.logger = logger

    def log(self, msg: str) -> None:
        if self.logger:
            try:
                self.logger(msg)
            except Exception:
                pass
        else:
            print(msg)

    def run_once(self) -> dict[str, Any]:
        self.log('autopoietic: starting iteration')
        recon = self.red_recon.discover()
        self.log(f'autopoietic: recon {recon}')
        crypto_findings = self.crypto.audit_crypto_wrappers()
        self.log(f'autopoietic: crypto {crypto_findings}')
        patch = self.blue.propose_patch(recon)
        verified = self.blue.formal_verify_patch(patch)
        self.log(f'autopoietic: patch {patch} verified={verified}')
        return {
            'recon': recon,
            'crypto': crypto_findings,
            'patch': patch,
            'verified': verified,
        }

    def run(self, iterations: int = 3, delay: float = 1.0):
        results = []
        for i in range(iterations):
            r = self.run_once()
            results.append(r)
            time.sleep(delay)
        return results
