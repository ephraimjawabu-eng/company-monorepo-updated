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
        errors = []

        # recon step
        try:
            recon = self.red_recon.discover()
            self.log(f'autopoietic: recon {recon}')
        except Exception as e:
            recon = {}
            errors.append(f'recon_error: {e}')
            self.log(f'autopoietic: recon error {e}')

        # crypto audit
        try:
            crypto_findings = self.crypto.audit_crypto_wrappers()
            self.log(f'autopoietic: crypto {crypto_findings}')
        except Exception as e:
            crypto_findings = []
            errors.append(f'crypto_error: {e}')
            self.log(f'autopoietic: crypto error {e}')

        # load detection rules (look in integrations dir for bundled rules)
        rules_dir = os.path.join(os.path.dirname(__file__), 'integrations')
        detections = []
        try:
            rules = detection_loader.load_rules_from_dir(rules_dir)
        except Exception as e:
            rules = []
            errors.append(f'rule_load_error: {e}')

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
            except Exception as e:
                errors.append(f'rule_eval_error:{r.get("id") or r.get("title")}:{e}')
                continue

        # propose patch and verify, but tolerate failures to keep loop alive
        try:
            patch = self.blue.propose_patch(recon)
        except Exception as e:
            patch = {}
            errors.append(f'patch_error: {e}')
            self.log(f'autopoietic: patch error {e}')

        try:
            verified = self.blue.formal_verify_patch(patch)
        except Exception as e:
            verified = False
            errors.append(f'verify_error: {e}')
            self.log(f'autopoietic: verify error {e}')

        self.log(f'autopoietic: patch {patch} verified={verified}')
        out = {
            'recon': recon,
            'crypto': crypto_findings,
            'detections': detections,
            'patch': patch,
            'verified': verified,
        }
        if errors:
            out['errors'] = errors
        return out
    def run(self, iterations: int = 3, delay: float = 1.0):
        results = []
        for i in range(iterations):
            r = self.run_once()
            results.append(r)
            time.sleep(delay)
        return results
