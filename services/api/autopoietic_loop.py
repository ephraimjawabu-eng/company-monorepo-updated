"""Orchestrator: runs red and blue agents in a closed loop and logs outcomes.
"""
from __future__ import annotations
import time
from typing import Any

from services.api.topology import GraphTopology
from services.api.agents_red import GraphReconAgent, CryptanalysisAgent
from services.api.agents_blue import AutopoieticHardenerAgent
from services.api.integrations import detection_loader
import os


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

        # load detection rules (look in integrations dir for bundled rules)
        rules_dir = os.path.join(os.path.dirname(__file__), 'integrations')
        detections = []
        try:
            rules = detection_loader.load_rules_from_dir(rules_dir)
        except Exception:
            rules = []
        # simple rule evaluation: topology rules like 'public->db'
        for r in rules:
            try:
                raw = r.get('raw') or {}
                if raw.get('type') == 'topology' or r.get('title','').lower().find('topo')!=-1:
                    cond = raw.get('condition') or raw.get('query') or r.get('title')
                    if isinstance(cond, str) and '->' in cond:
                        src, dst = cond.split('->', 1)
                        src = src.strip(); dst = dst.strip()
                        if self.topology.has_node(src) and self.topology.has_node(dst) and self.topology.reachable(src, dst):
                            detections.append({'rule': r.get('id') or r.get('title'), 'type': 'topology', 'desc': r.get('title') or cond, 'severity': raw.get('severity', 'medium')})
                else:
                    # fallback: look for rule text in crypto findings
                    txt = str(crypto_findings)
                    if r.get('title') and r.get('title').lower() in txt.lower():
                        detections.append({'rule': r.get('id') or r.get('title'), 'type': 'heuristic', 'desc': r.get('title')})
            except Exception:
                continue

        patch = self.blue.propose_patch(recon)
        verified = self.blue.formal_verify_patch(patch)
        self.log(f'autopoietic: patch {patch} verified={verified}')
        return {
            'recon': recon,
            'crypto': crypto_findings,
            'detections': detections,
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
