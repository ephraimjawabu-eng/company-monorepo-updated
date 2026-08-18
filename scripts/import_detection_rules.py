"""Import detection rules from a references directory into services/api/integrations/detections.

This script scans the references/ folder for JSON/YAML files containing detection-rule-like keys and copies them into the local detections directory.
"""
import os
import shutil
import json
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC = os.path.join(ROOT, 'references')
DST = os.path.join(ROOT, 'services', 'api', 'integrations', 'detections')

os.makedirs(DST, exist_ok=True)
count = 0
for root, dirs, files in os.walk(SRC):
    for f in files:
        if not f.lower().endswith(('.json', '.yml', '.yaml')):
            continue
        srcp = os.path.join(root, f)
        try:
            with open(srcp, 'r', encoding='utf-8', errors='ignore') as fh:
                obj = None
                if f.lower().endswith('.json'):
                    try:
                        obj = json.load(fh)
                    except Exception:
                        fh.seek(0)
                        try:
                            obj = yaml.safe_load(fh)
                        except Exception:
                            continue
                else:
                    try:
                        obj = yaml.safe_load(fh)
                    except Exception:
                        continue
                # heuristic: if object contains 'rule' or 'detection' or 'condition' keys
                if isinstance(obj, dict) and any(k in obj for k in ('rule_id','id','detection','condition','title','name')):
                    dstf = os.path.join(DST, f)
                    shutil.copyfile(srcp, dstf)
                    count += 1
        except Exception:
            continue
print(f"Imported {count} candidate rule files into {DST}")
