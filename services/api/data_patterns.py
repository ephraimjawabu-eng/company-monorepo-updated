"""Data engineering primitives: simple, well-documented reference implementations.

Note: These are small, opinionated demos for education, testing and CI smoke runs. They are
not production-grade; production behavior requires robust testing, durable storage, and
careful performance engineering.
"""
from collections import OrderedDict
import bisect
import os
import json
from typing import Any, List, Optional, Tuple


class LRUCache:
    """Simple LRU cache.

    Complexity:
      - get: O(1)
      - set: O(1)
    Space: O(capacity)
    """

    def __init__(self, capacity: int = 128):
        self.capacity = capacity
        self._data = OrderedDict()

    def get(self, key: Any, default: Any = None) -> Any:
        try:
            val = self._data.pop(key)
            # mark as recently used
            self._data[key] = val
            return val
        except KeyError:
            return default

    def set(self, key: Any, value: Any):
        if key in self._data:
            self._data.pop(key)
        elif len(self._data) >= self.capacity:
            # evict least recently used
            self._data.popitem(last=False)
        self._data[key] = value

    def __len__(self):
        return len(self._data)


class SortedIndex:
    """A tiny sorted-index that simulates B-tree-like behavior using a sorted list.

    Complexity (backed by list + bisect):
      - insert: O(n)
      - search: O(log n) for locating + O(1) for equality check
    Space: O(n)
    """

    def __init__(self):
        self._keys: List[Any] = []
        self._values: List[Any] = []

    def insert(self, key: Any, value: Any):
        i = bisect.bisect_left(self._keys, key)
        if i < len(self._keys) and self._keys[i] == key:
            self._values[i] = value
        else:
            self._keys.insert(i, key)
            self._values.insert(i, value)

    def get(self, key: Any) -> Optional[Any]:
        i = bisect.bisect_left(self._keys, key)
        if i < len(self._keys) and self._keys[i] == key:
            return self._values[i]
        return None

    def range_query(self, start: Any, end: Any) -> List[Tuple[Any, Any]]:
        i = bisect.bisect_left(self._keys, start)
        res = []
        while i < len(self._keys) and self._keys[i] <= end:
            res.append((self._keys[i], self._values[i]))
            i += 1
        return res


class SimpleLSM:
    """Illustrative LSM-like engine: memtable flushes to JSON files as 'sstables'.

    Complexity:
      - write: O(1) into memtable
      - read: O(#sstables + memtable lookup) naive
    Space: memtable + on-disk files
    """

    def __init__(self, storage_dir: str = 'data/lsm'):
        self.memtable = {}
        self.storage_dir = storage_dir
        os.makedirs(self.storage_dir, exist_ok=True)
        self.sstable_index = []  # list of filenames (newest last)

    def put(self, key: str, value: Any):
        self.memtable[key] = value

    def get(self, key: str) -> Optional[Any]:
        if key in self.memtable:
            return self.memtable[key]
        # search sstables from newest to oldest
        for fn in reversed(self.sstable_index):
            path = os.path.join(self.storage_dir, fn)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if key in data:
                    return data[key]
            except Exception:
                continue
        return None

    def flush(self):
        if not self.memtable:
            return None
        fn = f"sstable_{len(self.sstable_index)}.json"
        path = os.path.join(self.storage_dir, fn)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.memtable, f)
        self.sstable_index.append(fn)
        self.memtable = {}
        return fn


# Export a simple API for other modules
__all__ = ["LRUCache", "SortedIndex", "SimpleLSM"]
