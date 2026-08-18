"""Prune imported detection files to keep only those that look like detection rules.
Moves non-matching files to services/api/integrations/detections/ignored/ for manual review.
"""
import os
import shutil

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
DST = os.path.join(ROOT, 'services', 'api', 'integrations', 'detections')
IGN = os.path.join(DST, 'ignored')

os.makedirs(IGN, exist_ok=True)
count = 0
for fname in os.listdir(DST):
    full = os.path.join(DST, fname)
    if os.path.isdir(full):
        continue
    try:
        with open(full, 'r', encoding='utf-8', errors='ignore') as f:
            data = f.read()
        # heuristic: must include 'condition' or 'detection' or 'rule' or 'severity' or 'title'
        keys = ['condition', 'detection', 'rule', 'severity', 'title', 'id']
        if not any(k in data for k in keys):
            shutil.move(full, os.path.join(IGN, fname))
            count += 1
    except Exception:
        continue
print(f"Pruned {count} files to {IGN}")
