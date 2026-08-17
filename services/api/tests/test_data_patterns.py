from services.api.data_patterns import LRUCache, SortedIndex, SimpleLSM
import tempfile
import shutil


def test_lru_basic():
    c = LRUCache(capacity=2)
    c.set('a', 1)
    c.set('b', 2)
    assert c.get('a') == 1
    c.set('c', 3)
    # 'b' should be evicted because 'a' was recently used
    assert c.get('b') is None


def test_sorted_index():
    idx = SortedIndex()
    idx.insert(10, 'x')
    idx.insert(5, 'y')
    idx.insert(20, 'z')
    assert idx.get(10) == 'x'
    r = idx.range_query(5, 15)
    assert len(r) == 2


def test_simple_lsm(tmp_path):
    d = tmp_path / "lsmtest"
    storage = str(d)
    engine = SimpleLSM(storage_dir=storage)
    engine.put('k1', 'v1')
    engine.put('k2', 'v2')
    fn = engine.flush()
    assert fn is not None
    assert engine.get('k1') == 'v1'
    # after clearing memtable, get should still find in sstable
    engine.memtable = {}
    assert engine.get('k2') == 'v2'
