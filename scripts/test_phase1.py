"""Phase 1 acceptance tests."""
import sys
import tempfile
sys.path.insert(0, ".")

from core.database import DB
from core.models import Item

_tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp.close()
db = DB(_tmp.name)

# 1. All 4 tables
tables = {r[0] for r in db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
required = {"items", "sources", "yt_extracts", "collection_runs"}
missing = required - tables
print("tables present:", sorted(tables & required))
if missing:
    print("MISSING tables:", missing)
    sys.exit(1)

# 2. FTS virtual table
fts = db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='items_fts'").fetchone()
print("items_fts:", "ok" if fts else "MISSING")

# 3. store_items dedup
item = Item(
    url="https://example.com/xss-test",
    title="XSS via stored input",
    source_id="rss:abc123",
    source_type="rss",
    body="Cross-site scripting vulnerability in login form allows attackers to inject scripts.",
)
added1 = db.store_items([item])
added2 = db.store_items([item])
print(f"store_items first={added1} second(dedup)={added2}")
assert added1 == 1, f"expected 1 got {added1}"
assert added2 == 0, f"expected 0 got {added2}"

# 4. FTS query
results = db.get_items({"q": "xss"})
print(f"fts 'xss' results: {len(results)}")
assert len(results) >= 1, "FTS returned 0 results"

# 5. log_run + get_health
db.log_run({"items_added": added1, "errors": []})
h = db.get_health()
print(f"health: last_run={h.last_run} items_today={h.items_today} errors={h.errors}")
assert h.items_today >= 1

print("\nAll Phase 1 checks PASSED")
