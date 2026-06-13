from pathlib import Path
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from incremental_code_scan import analyze_scan, parse_unified_diff  # noqa: E402


SAMPLE_DIFF = """diff --git a/src/order/coupon.py b/src/order/coupon.py
index 1111111..2222222 100644
--- a/src/order/coupon.py
+++ b/src/order/coupon.py
@@ -8,0 +9,4 @@ def apply_coupon(order, coupon):
+    if coupon.min_spend <= order.total:
+        return apply_discount(order, coupon)
+    api_key = "secret-token"
+except:
"""


def test_parse_unified_diff_extracts_added_line_numbers_and_content():
    files = parse_unified_diff(SAMPLE_DIFF)

    assert len(files) == 1
    changed = files[0]
    assert changed["path"] == "src/order/coupon.py"
    assert changed["status"] == "modified"
    assert [line["new_line"] for line in changed["added_lines"]] == [9, 10, 11, 12]
    assert changed["added_lines"][0]["content"] == "    if coupon.min_spend <= order.total:"


def test_analyze_scan_maps_incremental_lines_to_prd_and_bug_risks(tmp_path):
    prd = tmp_path / "coupon_prd.md"
    prd.write_text(
        "# Coupon PRD\n\n"
        "- REQ-COUPON-001: 优惠券 coupon 必须校验 min_spend 后才能 apply discount。\n"
        "- REQ-SEC-001: 代码不得新增 hardcoded secret。\n",
        encoding="utf-8",
    )

    result = analyze_scan(SAMPLE_DIFF, prd_text=prd.read_text(encoding="utf-8"))

    assert result["summary"]["changed_files"] == 1
    assert result["summary"]["added_lines"] == 4

    first_line = result["files"][0]["added_lines"][0]
    assert first_line["prd_alignment"]["status"] == "matched"
    assert first_line["prd_alignment"]["requirement_ids"] == ["REQ-COUPON-001"]

    risks = result["potential_bugs"]
    assert {risk["rule_id"] for risk in risks} >= {"HARDCODED_SECRET", "BARE_EXCEPT"}
    assert any(risk["requirement_ids"] == ["REQ-SEC-001"] for risk in risks)
