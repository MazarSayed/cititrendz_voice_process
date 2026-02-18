"""
Tiny smoke helper (no app/server yet).

This is intentionally minimal and only validates that the LangGraph scaffold compiles.
"""

from __future__ import annotations

from .graph import build_graph, state_to_dict
from .state import new_session_state


def main() -> None:
    graph = build_graph()
    state = new_session_state(session_id="sess_demo")
    # 1) First run: should prompt for PO/carton.
    out1 = graph.invoke(state)
    print("OUT1", out1.get("current_node"), out1.get("last_prompt"))

    # 2) Simulate resume: user spoke PO number.
    out1["last_user_input"] = {"client_action_id": "a1", "transcript": "PO 123456"}
    out2 = graph.invoke(out1)
    print("OUT2", out2.get("current_node"), {"po_number": out2.get("po_number")})

    # 3) Next invoke should prompt for Confirm/Mismatch.
    out3 = graph.invoke(out2)
    print("OUT3", out3.get("current_node"), out3.get("last_prompt"))

    # 4) Simulate resume: user confirms.
    out3["last_user_input"] = {"client_action_id": "a2", "transcript": "Confirm"}
    out4 = graph.invoke(out3)
    print("OUT4", out4.get("current_node"), {"po_verification_result": out4.get("po_verification_result")})

    # 5) Next invoke should prompt for carton condition.
    out5 = graph.invoke(out4)
    print("OUT5", out5.get("current_node"), out5.get("last_prompt"))

    # 6) Simulate resume: carton ok.
    out5["last_user_input"] = {"client_action_id": "a3", "transcript": "Carton OK"}
    out6 = graph.invoke(out5)
    print("OUT6", out6.get("current_node"), {"carton_status": out6.get("carton_status")})

    # 7) Next invoke should prompt for style/SKU scan or manual entry.
    out7 = graph.invoke(out6)
    print("OUT7", out7.get("current_node"), out7.get("last_prompt"))

    # 8) Simulate resume: manual entry style.
    out7["last_user_input"] = {"client_action_id": "a4", "transcript": "Manual entry. Style 48792"}
    out8 = graph.invoke(out7)
    print("OUT8", out8.get("current_node"), {"style_id": out8.get("style_id"), "method": out8.get("style_entry_method")})

    # 9) Next invoke should prompt for color/size match.
    out9 = graph.invoke(out8)
    print("OUT9", out9.get("current_node"), out9.get("last_prompt"))

    # 10) Simulate resume: match.
    out9["last_user_input"] = {"client_action_id": "a5", "transcript": "Match"}
    out10 = graph.invoke(out9)
    print("OUT10", out10.get("current_node"), {"color_size_match": out10.get("color_size_match")})

    # 11) Next invoke should prompt for unit counts by size.
    out11 = graph.invoke(out10)
    print("OUT11", out11.get("current_node"), out11.get("last_prompt"))

    # 12) Simulate resume: size counts.
    out11["last_user_input"] = {
        "client_action_id": "a6",
        "transcript": "Small 8. Medium 12. Large 16. Extra-large 12.",
    }
    out12 = graph.invoke(out11)
    print("OUT12", out12.get("current_node"), {"size_counts": out12.get("size_counts"), "total": out12.get("total_units_counted")})

    # 13) Next invoke should prompt for defect inspection.
    out13 = graph.invoke(out12)
    print("OUT13", out13.get("current_node"), out13.get("last_prompt"))

    # 14) Simulate resume: all units ok.
    out13["last_user_input"] = {"client_action_id": "a7", "transcript": "All units OK"}
    out14 = graph.invoke(out13)
    print("OUT14", out14.get("current_node"), {"all_units_ok": out14.get("all_units_ok"), "defects": out14.get("defects")})

    # 15) Next invoke should prompt for tags/labeling.
    out15 = graph.invoke(out14)
    print("OUT15", out15.get("current_node"), out15.get("last_prompt"))

    # 16) Simulate resume: tags ok.
    out15["last_user_input"] = {"client_action_id": "a8", "transcript": "Tags OK"}
    out16 = graph.invoke(out15)
    print("OUT16", out16.get("current_node"), {"tags_ok": out16.get("tags_ok"), "tags_issues": out16.get("tags_issues")})

    # 17) Next invoke should prompt for packaging/presentation.
    out17 = graph.invoke(out16)
    print("OUT17", out17.get("current_node"), out17.get("last_prompt"))

    # 18) Simulate resume: packaging ok.
    out17["last_user_input"] = {"client_action_id": "a9", "transcript": "Packaging OK"}
    out18 = graph.invoke(out17)
    print("OUT18", out18.get("current_node"), {"packaging_ok": out18.get("packaging_ok"), "packaging_issues": out18.get("packaging_issues")})

    # 19) Next invoke should skip photos (no exceptions) and go to disposition.
    out19 = graph.invoke(out18)
    print("OUT19", out19.get("current_node"), out19.get("last_prompt"))

    # 20) Next invoke should prompt for disposition.
    out20 = graph.invoke(out19)
    print("OUT20", out20.get("current_node"), out20.get("last_prompt"))

    # 21) Simulate resume: Accept.
    out20["last_user_input"] = {"client_action_id": "a10", "transcript": "Accept"}
    out21 = graph.invoke(out20)
    print("OUT21", out21.get("current_node"), {"disposition": out21.get("disposition")})

    # 22) Next invoke should prompt for notes.
    out22 = graph.invoke(out21)
    print("OUT22", out22.get("current_node"), out22.get("last_prompt"))

    # 23) Simulate resume: No notes.
    out22["last_user_input"] = {"client_action_id": "a11", "transcript": "No notes"}
    out23 = graph.invoke(out22)
    print("OUT23", out23.get("current_node"), {"notes": out23.get("notes")})

    # 24) Next invoke should prompt for Next style / Close PO.
    out24 = graph.invoke(out23)
    print("OUT24", out24.get("current_node"), out24.get("last_prompt"))

    # 25) Simulate resume: Close PO.
    out24["last_user_input"] = {"client_action_id": "a12", "transcript": "Close PO"}
    out25 = graph.invoke(out24)
    print("OUT25", out25.get("current_node"), {"completed_styles": out25.get("completed_styles")})

    # 26) One more invoke to see close prompt.
    out26 = graph.invoke(out25)
    print("OUT26", out26.get("current_node"), out26.get("last_prompt"))


if __name__ == "__main__":
    main()

