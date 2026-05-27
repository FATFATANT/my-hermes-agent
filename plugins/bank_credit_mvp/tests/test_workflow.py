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


def test_poll_cases_advances_ready_external_work(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    import importlib
    import plugins.bank_credit_mvp.workflow as workflow

    workflow = importlib.reload(workflow)
    case = workflow.reset_demo()
    blocked = workflow.advance_case(case["id"])
    assert blocked["status"] == "blocked"

    poll_before = workflow.poll_cases()
    assert poll_before["checked"] == 1
    assert workflow.get_case(case["id"])["status"] == "blocked"

    workflow.mark_customer_created(case["id"], "CUST-20002")
    completed = workflow.get_case(case["id"])
    assert completed["status"] == "completed"

    poll_after = workflow.poll_cases()
    assert poll_after["checked"] == 0
