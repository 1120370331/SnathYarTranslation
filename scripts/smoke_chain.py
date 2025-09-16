"""
Smoke test: Chinese → Shathyar (AI/mock) → confirm edit → Shathyar → Chinese

Runs against a live backend at http://localhost:8000 with SHATHYAR_AI_MOCK enabled.
Exits with code 0 on success, non‑zero on failure.
"""

import sys
import time
import json
from typing import Any, Dict

import urllib.request


BASE = "http://localhost:8000/api/v1"


def post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE}{path}",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "ignore")
        print(f"HTTP {e.code} for {path}: {body}", file=sys.stderr)
        raise


def main() -> int:
    cn_text = f"链路确认测试——编辑后应可反向翻译 {int(time.time())}"

    # 1) CN -> SH (mock AI)
    tr = post("/translate", {"text": cn_text, "source_language": "chinese"})
    assert tr.get("translated_text"), "missing translated_text"
    assert tr.get("translation_id"), f"missing translation_id (resp={tr})"
    assert tr.get("can_edit") is True, f"must be editable (resp={tr})"

    tid = tr["translation_id"]
    edited = tr["translated_text"] + "'ah"  # small deterministic edit

    # 2) Confirm with edited text
    conf = post(f"/translate/{tid}/confirm", {"edited_text": edited})
    assert conf.get("translated_text") == edited, "confirm did not return edited text"

    # 3) SH -> CN reverse lookup must return original Chinese
    rev = post("/translate", {"text": edited, "source_language": "shathyar"})
    assert rev.get("translated_text") == cn_text, (
        f"reverse translation mismatch: {rev.get('translated_text')} != {cn_text}"
    )
    print("✓ Smoke chain passed")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"Smoke chain failed: {e}", file=sys.stderr)
        sys.exit(1)
