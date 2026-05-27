from pathlib import Path


def test_workflow_blocks_then_completes(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    import importlib
    import plugins.bank_credit_mvp.workflow as workflow

    workflow = importlib.reload(workflow)
    case = workflow.reset_demo()

    blocked = workflow.advance_case(case["id"])
    assert blocked["status"] == "blocked"
    assert blocked["current_step"] == "open_customer_no"
    assert blocked["steps"][0]["status"] == "action_required"

    completed = workflow.mark_customer_created(case["id"], "CUST-10001")
    assert completed["status"] == "completed"
    assert completed["report_fields"]["customer_no"] == "CUST-10001"
    assert completed["steps"][1]["status"] == "completed"
    assert completed["steps"][2]["status"] == "skipped"
    assert completed["steps"][3]["status"] == "completed"

    assert (Path(tmp_path) / "plugins" / "bank-credit-mvp" / "state.json").exists()
