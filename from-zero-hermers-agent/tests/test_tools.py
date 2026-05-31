from hermers_agent.tools.registry import builtin_registry


def test_builtin_registry_can_filter_toolsets():
    registry = builtin_registry({"core"})

    assert [tool.name for tool in registry.list_tools()] == ["echo"]
    assert [schema["function"]["name"] for schema in registry.schemas()] == ["echo"]


def test_file_tools_can_read_and_search(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "notes.txt").write_text("alpha\nbeta\nalpha again\n")
    registry = builtin_registry({"files"})

    assert registry.call("read_file", {"path": "notes.txt"}) == "alpha\nbeta\nalpha again\n"
    assert registry.call("search_files", {"query": "alpha", "path": ".", "limit": 1}) == (
        "notes.txt:1: alpha"
    )


def test_search_files_returns_matches_below_limit(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "notes.txt").write_text("alpha\nbeta\n")
    registry = builtin_registry({"files"})

    assert registry.call("search_files", {"query": "beta", "path": "notes.txt"}) == (
        "notes.txt:2: beta"
    )
