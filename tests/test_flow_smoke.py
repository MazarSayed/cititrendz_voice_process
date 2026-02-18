from __future__ import annotations

from cititrends_voice_process.graph import build_graph
from cititrends_voice_process.state import new_session_state


def test_first_three_steps_happy_path() -> None:
    g = build_graph()
    s = new_session_state("sess_test")

    # Step 0 prompt
    s = g.invoke(s)
    assert s["current_node"] == "START_IDENTIFICATION"
    assert "Scan the carton barcode" in (s.get("last_prompt") or {}).get("text", "")

    # Provide PO
    s["last_user_input"] = {"client_action_id": "t1", "transcript": "PO 123456"}
    s = g.invoke(s)
    assert s["current_node"] == "PO_CARTON_VERIFICATION"
    assert s["po_number"] == "123456"

    # Step 1 prompt
    s = g.invoke(s)
    assert s["current_node"] == "PO_CARTON_VERIFICATION"
    assert "Confirm" in (s.get("last_prompt") or {}).get("text", "")

    # Confirm
    s["last_user_input"] = {"client_action_id": "t2", "transcript": "Confirm"}
    s = g.invoke(s)
    assert s["current_node"] == "CARTON_CONDITION"
    assert s["po_verification_result"] == "CONFIRMED"

    # Step 2 prompt then carton ok
    s = g.invoke(s)
    s["last_user_input"] = {"client_action_id": "t3", "transcript": "Carton OK"}
    s = g.invoke(s)
    assert s["current_node"] == "STYLE_SKU_VERIFICATION"
    assert s["carton_status"] == "OK"

    # Step 3 prompt then manual entry style
    s = g.invoke(s)
    assert s["current_node"] == "STYLE_SKU_VERIFICATION"
    assert "Scan the first item barcode" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t4", "transcript": "Manual entry. Style 48792"}
    s = g.invoke(s)
    assert s["current_node"] == "COLOR_SIZE_VERIFICATION"
    style = s.get("current_style") or {}
    assert style["style_id"] == "48792"
    assert style["style_entry_method"] == "MANUAL"

    # Step 4 prompt then match
    s = g.invoke(s)
    assert s["current_node"] == "COLOR_SIZE_VERIFICATION"
    assert "Verify color and size" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t5", "transcript": "Match"}
    s = g.invoke(s)
    assert s["current_node"] == "UNIT_COUNT_BY_SIZE"
    style = s.get("current_style") or {}
    assert style["color_size_match"] is True

    # Step 5 prompt then size counts
    s = g.invoke(s)
    assert s["current_node"] == "UNIT_COUNT_BY_SIZE"
    assert "Count units by size" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {
        "client_action_id": "t6",
        "transcript": "Small 8. Medium 12. Large 16. Extra-large 12.",
    }
    s = g.invoke(s)
    assert s["current_node"] == "DEFECT_INSPECTION_100pct"
    style = s.get("current_style") or {}
    assert style["total_units_counted"] == 48
    # basic structure check
    assert any(x["size"] == "S" and x["qty"] == 8 for x in style["size_counts"])

    # Step 6 prompt then all units ok
    s = g.invoke(s)
    assert s["current_node"] == "DEFECT_INSPECTION_100pct"
    assert "Inspect every unit" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t7", "transcript": "All units OK"}
    s = g.invoke(s)
    assert s["current_node"] == "TAGS_LABELING"
    style = s.get("current_style") or {}
    assert style["all_units_ok"] is True
    assert style["defects"] == []

    # Step 7 prompt then tags ok
    s = g.invoke(s)
    assert s["current_node"] == "TAGS_LABELING"
    assert "Check tickets and labels" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t8", "transcript": "Tags OK"}
    s = g.invoke(s)
    assert s["current_node"] == "PACKAGING_PRESENTATION"
    style = s.get("current_style") or {}
    assert style["tags_ok"] is True
    assert style["tags_issues"] == []

    # Step 8 prompt then packaging ok
    s = g.invoke(s)
    assert s["current_node"] == "PACKAGING_PRESENTATION"
    assert "Check packaging requirements" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t9", "transcript": "Packaging OK"}
    s = g.invoke(s)
    assert s["current_node"] == "PHOTO_CAPTURE_LOOP"
    style = s.get("current_style") or {}
    assert style["packaging_ok"] is True
    assert style["packaging_issues"] == []

    # Step 9: no exceptions -> skip photos to disposition
    s = g.invoke(s)
    assert s["current_node"] == "DISPOSITION"
    assert "Proceeding to disposition" in (s.get("last_prompt") or {}).get("text", "")

    # Step 10: disposition prompt then accept
    s = g.invoke(s)
    assert s["current_node"] == "DISPOSITION"
    assert "State disposition" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t10", "transcript": "Accept"}
    s = g.invoke(s)
    assert s["current_node"] == "NOTES_OPTIONAL"
    assert s["disposition"] == "ACCEPT"

    # Step 11: notes optional
    s = g.invoke(s)
    assert s["current_node"] == "NOTES_OPTIONAL"
    assert "Add notes if needed" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t11", "transcript": "No notes"}
    s = g.invoke(s)
    assert s["current_node"] == "COMPLETE_STYLE"
    style = s.get("current_style") or {}
    assert style.get("notes", "") == ""

    # Step 12: complete style
    s = g.invoke(s)
    assert s["current_node"] == "COMPLETE_STYLE"
    assert "Inspection complete for this style" in (s.get("last_prompt") or {}).get("text", "")

    s["last_user_input"] = {"client_action_id": "t12", "transcript": "Close PO"}
    s = g.invoke(s)
    assert s["current_node"] == "CLOSE_PO"
    assert s["completed_styles"] == 1

