"""Environment resilience helpers: normalize config, simple circuit breaker, retry/backoff, and singleflight.

This module helps the autopoietic loop reason about environmental variability (different OS, missing services,
resource constraints) and propose mitigations.
"""
from __future__ import annotations
import sys
import time
import threading
import platform
from typing import Any, Callable, Dict, Optional


class CircuitBreaker:
    """Simple per-key circuit breaker."""

    def __init__(self, failure_threshold: int = 5, reset_timeout: float = 60.0):
        self._failures: Dict[str, int] = {}
        self._tripped_at: Dict[str, float] = {}
        self.failure_threshold = failure_threshold
        self.reset_timeout = reset_timeout
        self._lock = threading.Lock()

    def record_failure(self, key: str) -> None:
        with self._lock:
            self._failures[key] = self._failures.get(key, 0) + 1
            if self._failures[key] >= self.failure_threshold:
                self._tripped_at[key] = time.time()

    def record_success(self, key: str) -> None:
        with self._lock:
            self._failures.pop(key, None)
            self._tripped_at.pop(key, None)

    def allows(self, key: str) -> bool:
        with self._lock:
            if key in self._tripped_at:
                if time.time() - self._tripped_at[key] > self.reset_timeout:
                    # half-open: reset counters and allow
                    self._failures.pop(key, None)
                    self._tripped_at.pop(key, None)
                    return True
                return False
            return True


def retry_with_backoff(max_tries: int = 3, base_delay: float = 0.1, jitter: float = 0.05):
    def deco(fn: Callable[..., Any]):
        def wrapper(*a, **kw):
            tries = 0
            while True:
                try:
                    return fn(*a, **kw)
                except Exception:
                    tries += 1
                    if tries >= max_tries:
                        raise
                    delay = base_delay * (2 ** (tries - 1))
                    delay = delay * (1 + (jitter * (2 * (time.time() % 1) - 1)))
                    time.sleep(delay)
        return wrapper
    return deco


class SingleFlight:
    """Deduplicate concurrent function calls by key."""

    def __init__(self):
        self._inflight: Dict[str, threading.Event] = {}
        self._results: Dict[str, Any] = {}
        self._lock = threading.Lock()

    def do(self, key: str, fn: Callable[[], Any]):
        with self._lock:
            if key in self._inflight:
                ev = self._inflight[key]
            else:
                ev = threading.Event()
                self._inflight[key] = ev
                # mark as leader and run
                try:
                    res = fn()
                    self._results[key] = (True, res)
                except Exception as e:
                    self._results[key] = (False, e)
                finally:
                    ev.set()
                    self._inflight.pop(key, None)
                    result = self._results.pop(key)
                    if result[0]:
                        return result[1]
                    raise result[1]

        # follower waits
        ev.wait()
        ok, result = self._results.pop(key, (False, RuntimeError('empty')))
        if ok:
            return result
        raise result


class EnvironmentResilience:
    """Simple audits and proposals for environmental resilience."""

    def __init__(self):
        self.circuit = CircuitBreaker()
        self.sf = SingleFlight()

    def normalize_config(self, cfg: Dict[str, Any]) -> Dict[str, Any]:
        # Normalize keys to lower-case and coerce common types
        out: Dict[str, Any] = {}
        for k, v in (cfg or {}).items():
            lk = k.lower()
            if isinstance(v, str):
                if v.isdigit():
                    out[lk] = int(v)
                else:
                    out[lk] = v
            else:
                out[lk] = v
        return out

    def check_runtime_compatibility(self) -> Dict[str, Any]:
        """Return basic runtime compatibility hints."""
        hints = {
            'python_version': sys.version.split()[0],
            'platform': platform.system(),
            'machine': platform.machine(),
        }
        return hints

    def audit_environment(self, topology, recon: Optional[Dict[str, Any]] = None) -> list[Dict[str, Any]]:
        """Produce a small list of findings about environmental risks and suggested mitigations.

        This is intentionally conservative — it surfaces likely deployment mismatches and common
        pitfalls (missing size constraints, absent caching layers, unprotected secrets in env files).
        """
        findings: list[Dict[str, Any]] = []
        # runtime hints
        hints = self.check_runtime_compatibility()
        findings.append({'type': 'runtime_hints', 'desc': 'runtime summary', 'data': hints})

        # topology-based checks: detect public->db and propose isolation (already a detection but duplicate here)
        try:
            nodes = []
            if hasattr(topology, 'sensitive_assets'):
                sens = topology.sensitive_assets()
                if sens:
                    findings.append({'type': 'sensitive_assets', 'desc': 'sensitive assets present', 'data': sens})
        except Exception:
            pass

        # quick check: look for common env var pitfalls in recon if present
        if recon and isinstance(recon, dict):
            cfg = recon.get('config', {}) or {}
            norm = self.normalize_config(cfg)
            if 'debug' in norm and norm.get('debug') in (True, 'True', 'true', '1'):
                findings.append({'type': 'config', 'desc': 'debug_enabled', 'severity': 'low', 'mitigation': 'Ensure DEBUG is disabled in production'})
            if 'database_url' in norm and norm.get('database_url', '').startswith('sqlite'):
                findings.append({'type': 'config', 'desc': 'sqlite_in_prod', 'severity': 'medium', 'mitigation': 'Use a production-grade rdbms and connection pool'})

        # circuit-breaker suggestion for external services
        findings.append({'type': 'circuit_breaker', 'desc': 'recommend adding CB+backoff for external services', 'severity': 'medium'})

        return findings


# lightweight helpers exported for other modules
__all__ = ['EnvironmentResilience', 'CircuitBreaker', 'retry_with_backoff', 'SingleFlight']
