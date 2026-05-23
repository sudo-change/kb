"""Phase 5 acceptance tests — MCP Server.

Requires:
  - API running: uvicorn api.main:app --port 8000
  - At least 1 item in DB (run collector first or: python collector/main.py --once)

Run from repo root:
  python scripts/test_phase5.py
"""

from __future__ import annotations

import sys

sys.path.insert(0, ".")

# --------------------------------------------------------------------------- #
# 1. Server module imports cleanly
# --------------------------------------------------------------------------- #
try:
    from mcp_server.server import (
        CATEGORIES,
        classify_item,
        get_categories,
        get_daily_digest,
        get_items,
        get_youtube_transcript,
    )
    print("[+] mcp_server.server imports OK")
except ImportError as e:
    print(f"[FAIL] import error: {e}")
    sys.exit(1)

# --------------------------------------------------------------------------- #
# 2. get_categories — no API needed
# --------------------------------------------------------------------------- #
cats = get_categories()
assert isinstance(cats, list), "get_categories must return list"
assert "BugBounty" in cats, "'BugBounty' missing"
assert len(cats) == 7, f"expected 7 categories, got {len(cats)}"
print(f"[+] get_categories: {cats}")

# --------------------------------------------------------------------------- #
# 3. get_items — requires running API
# --------------------------------------------------------------------------- #
try:
    items_24h = get_items(time_range="24h")
    assert isinstance(items_24h, list), "get_items must return list"
    print(f"[+] get_items(time_range='24h'): {len(items_24h)} items")

    items_bb = get_items(time_range="30d", category="BugBounty")
    assert isinstance(items_bb, list), "get_items(category=BugBounty) must return list"
    for item in items_bb:
        assert item.get("category") == "BugBounty", f"wrong category: {item.get('category')}"
    print(f"[+] get_items(category='BugBounty'): {len(items_bb)} items")

    # Invalid category must raise
    try:
        get_items(category="NotACategory")
        print("[FAIL] get_items(invalid category) should have raised")
        sys.exit(1)
    except ValueError:
        print("[+] get_items(invalid category) raises ValueError correctly")

except Exception as e:
    print(f"[FAIL] get_items: {e}")
    print("       Is the API running? uvicorn api.main:app --port 8000")
    sys.exit(1)

# --------------------------------------------------------------------------- #
# 4. classify_item — requires running API + item with id=1
# --------------------------------------------------------------------------- #
try:
    items_any = get_items(time_range="90d", limit=1)
    if not items_any:
        print("[SKIP] classify_item: no items in DB — run collector first")
    else:
        item_id = items_any[0]["id"]
        original_cat = items_any[0].get("category")

        updated = classify_item(item_id=item_id, category="BugBounty")
        assert updated["id"] == item_id, "returned wrong item"
        assert updated["category"] == "BugBounty", f"category not updated: {updated['category']}"
        print(f"[+] classify_item(item_id={item_id}, category='BugBounty') -> OK")

        # Restore original category if it was set
        if original_cat and original_cat in CATEGORIES:
            classify_item(item_id=item_id, category=original_cat)

        # Invalid category must raise
        try:
            classify_item(item_id=item_id, category="InvalidCat")
            print("[FAIL] classify_item(invalid category) should have raised")
            sys.exit(1)
        except ValueError:
            print("[+] classify_item(invalid category) raises ValueError correctly")

except Exception as e:
    print(f"[FAIL] classify_item: {e}")
    sys.exit(1)

# --------------------------------------------------------------------------- #
# 5. get_daily_digest — requires running API
# --------------------------------------------------------------------------- #
try:
    digest = get_daily_digest()
    assert isinstance(digest, dict), "get_daily_digest must return dict"
    for cat, rows in digest.items():
        assert isinstance(rows, list), f"digest[{cat}] must be list"
        for item in rows:
            assert item.get("category") == cat or cat == "Uncategorized", (
                f"item in bucket '{cat}' has category '{item.get('category')}'"
            )
    total = sum(len(v) for v in digest.values())
    print(f"[+] get_daily_digest: {len(digest)} non-empty categories, {total} total items")
except Exception as e:
    print(f"[FAIL] get_daily_digest: {e}")
    sys.exit(1)

# --------------------------------------------------------------------------- #
# 6. get_youtube_transcript — optional (requires yt-dlp + network)
# --------------------------------------------------------------------------- #
import shutil
if shutil.which("yt-dlp") and shutil.which("node"):
    test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"  # short ~18s video
    try:
        md = get_youtube_transcript(test_url)
        assert isinstance(md, str) and len(md) > 100, "transcript too short"
        print(f"[+] get_youtube_transcript: {len(md)} chars returned")
    except Exception as e:
        print(f"[WARN] get_youtube_transcript: {e}")
        print("       Non-fatal — YT extraction depends on network/cookies")
else:
    print("[SKIP] get_youtube_transcript: yt-dlp or node not on PATH")

print("\nAll Phase 5 checks PASSED")
