import copy
import importlib


def _case(status="blocked", current_step="open_customer_no"):
    return {
        "id": "loan-demo-001",
        "applicant_name": "上海青禾贸易有限公司",
        "amount": 500000,
        "purpose": "流动资金周转",
        "status": status,
        "current_step": current_step,
        "progress": 0.17,
        "steps": [
            {"id": "open_customer_no", "title": "开立客户号", "status": "action_required", "external_url": "/customer/open"},
            {"id": "fill_investigation_report", "title": "填写调查报告基础要素", "status": "pending", "external_url": "/credit/report"},
            {"id": "risk_admission_review", "title": "风险准入复核", "status": "pending", "external_url": "/risk/admission"},
            {"id": "sync_financial_data", "title": "同步财报数据", "status": "pending", "external_url": "/financials"},
            {"id": "collateral_confirmation", "title": "担保/抵押落实确认", "status": "pending", "external_url": "/collateral/confirm"},
            {"id": "save_report", "title": "保存调查报告草稿", "status": "pending", "external_url": "/credit/save"},
        ],
        "report_fields": {"customer_no": None},
        "events": [],
    }


def test_workflow_reads_cases_from_external_bank_system(monkeypatch):
    import plugins.bank_credit_mvp.workflow as workflow

    workflow = importlib.reload(workflow)
    calls = []

    def fake_request(method, path, payload=None):
        calls.append((method, path, payload))
        if method == "GET" and path == "/api/bank/credit-cases":
            return {"cases": [_case()]}
        raise AssertionError((method, path, payload))

    monkeypatch.setattr(workflow, "_request", fake_request)
    cases = workflow.list_cases()

    assert calls == [("GET", "/api/bank/credit-cases", None)]
    assert cases[0]["id"] == "loan-demo-001"
    assert cases[0]["steps"][0]["external_url"].startswith("http://127.0.0.1:5174/customer/open")


def test_advance_case_posts_to_external_bank_system(monkeypatch):
    import plugins.bank_credit_mvp.workflow as workflow

    workflow = importlib.reload(workflow)
    posted = {}

    def fake_request(method, path, payload=None):
        posted["method"] = method
        posted["path"] = path
        posted["payload"] = payload
        case = _case(status="blocked", current_step="risk_admission_review")
        case["steps"][0]["status"] = "completed"
        case["report_fields"]["customer_no"] = "CUST-10001"
        return {"success": True, "case": case}

    monkeypatch.setattr(workflow, "_request", fake_request)
    advanced = workflow.advance_case("loan-demo-001", {"purpose": "采购原材料"})

    assert posted == {
        "method": "POST",
        "path": "/api/bank/credit-cases/loan-demo-001/advance",
        "payload": {"report_fields": {"purpose": "采购原材料"}},
    }
    assert advanced["current_step"] == "risk_admission_review"
    assert advanced["report_fields"]["customer_no"] == "CUST-10001"


def test_delete_case_uses_external_bank_system(monkeypatch):
    import plugins.bank_credit_mvp.workflow as workflow

    workflow = importlib.reload(workflow)

    def fake_request(method, path, payload=None):
        assert method == "DELETE"
        assert path == "/api/bank/credit-cases/loan-demo-001"
        assert payload is None
        return {"success": True, "deleted": True, "case_id": "loan-demo-001"}

    monkeypatch.setattr(workflow, "_request", fake_request)
    assert workflow.delete_case("loan-demo-001") == {"deleted": True, "case_id": "loan-demo-001"}


def test_poll_cases_delegates_to_external_bank_system(monkeypatch):
    import plugins.bank_credit_mvp.workflow as workflow

    workflow = importlib.reload(workflow)
    expected = {"checked": 1, "changed": 1, "results": [{"case_id": "loan-demo-001", "changed": True}]}

    def fake_request(method, path, payload=None):
        assert (method, path, payload) == ("POST", "/api/bank/credit-cases/poll", None)
        return {"success": True, "poll": copy.deepcopy(expected)}

    monkeypatch.setattr(workflow, "_request", fake_request)
    assert workflow.poll_cases() == expected


def test_session_case_links_are_many_to_many(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))

    import plugins.bank_credit_mvp.workflow as workflow

    workflow = importlib.reload(workflow)
    workflow.associate_session_case("session-a", "loan-001")
    workflow.associate_session_case("session-a", "loan-002")
    workflow.associate_session_case("session-b", "loan-001")

    assert workflow.session_case_ids("session-a") == ["loan-001", "loan-002"]
    assert workflow.session_case_ids("session-b") == ["loan-001"]

    workflow.dissociate_session_case("session-a", "loan-001")
    assert workflow.session_case_ids("session-a") == ["loan-002"]
    assert workflow.hidden_session_case_ids("session-a") == ["loan-001"]

    workflow.associate_session_case("session-a", "loan-001")
    assert workflow.session_case_ids("session-a") == ["loan-002", "loan-001"]
    assert workflow.hidden_session_case_ids("session-a") == []


def test_mock_customer_tool_is_not_exposed_to_agent():
    import plugins.bank_credit_mvp.tools as tools

    tool_names = [item[0] for item in tools.TOOLS]
    assert "bank_credit_create_case" in tool_names
    assert "bank_credit_mock_customer_created" not in tool_names


def test_create_case_requires_explicit_confirmation(monkeypatch):
    import plugins.bank_credit_mvp.tools as tools

    called = False
    tools._PENDING_CREATES.clear()

    def fake_create_case(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(tools.workflow, "create_case", fake_create_case)
    result = tools._create_case({
        "applicant_name": "上海青禾贸易有限公司",
        "amount": 500000,
        "purpose": "流动资金周转",
    })

    assert '"needs_confirmation": true' in result
    assert not called


def test_create_case_first_confirmed_call_only_stages_draft(monkeypatch):
    import plugins.bank_credit_mvp.tools as tools

    called = False
    tools._PENDING_CREATES.clear()

    def fake_create_case(*_args, **_kwargs):
        nonlocal called
        called = True

    monkeypatch.setattr(tools.workflow, "create_case", fake_create_case)
    result = tools._create_case({
        "applicant_name": "上海青禾贸易有限公司",
        "amount": 500000,
        "purpose": "流动资金周转",
        "confirmed": True,
    }, task_id="session-a")

    assert '"needs_confirmation": true' in result
    assert not called


def test_create_case_creates_after_staged_draft_is_confirmed(monkeypatch):
    import plugins.bank_credit_mvp.tools as tools

    tools._PENDING_CREATES.clear()
    created = {}

    def fake_create_case(applicant_name, amount, purpose):
        created.update({
            "applicant_name": applicant_name,
            "amount": amount,
            "purpose": purpose,
        })
        return {"id": "LOAN-0002"}

    monkeypatch.setattr(tools.workflow, "create_case", fake_create_case)
    monkeypatch.setattr(tools.workflow, "associate_session_case", lambda *_args: None)
    args = {
        "applicant_name": "上海青禾贸易有限公司",
        "amount": 500000,
        "purpose": "流动资金周转",
    }

    tools._create_case(args, task_id="session-a")
    result = tools._create_case({**args, "confirmed": True}, task_id="session-a")

    assert '"success": true' in result
    assert created == {
        "applicant_name": "上海青禾贸易有限公司",
        "amount": 500000,
        "purpose": "流动资金周转",
    }
