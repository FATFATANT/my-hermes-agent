from hermers_agent.cli import main


def test_cli_chat_saves_session(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))

    assert main(["chat", "hello"]) == 0

    output = capsys.readouterr().out
    assert "[local/echo] hello" in output
    assert "[session:" in output


def test_cli_chat_accepts_one_turn_model_override(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text("model: remote/model\n")

    assert main(["chat", "--model", "local/echo", "hello"]) == 0

    output = capsys.readouterr().out
    assert "[local/echo] hello" in output


def test_cli_chat_can_disable_tools_for_one_turn(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))

    assert main(["chat", "--no-tools", "/tool", "echo", "hello"]) == 0

    output = capsys.readouterr().out
    assert "Unknown tool: echo. Available tools: none" in output


def test_cli_chat_can_select_toolsets(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    (tmp_path / "notes.txt").write_text("hello from file")

    assert main(["chat", "--toolset", "files", "/tool", "read_file", '{"path": "notes.txt"}']) == 0

    output = capsys.readouterr().out
    assert "hello from file" in output


def test_cli_lists_tool_schemas_as_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))

    assert main(["tools", "--json"]) == 0

    output = capsys.readouterr().out
    assert '"type": "function"' in output
    assert '"name": "echo"' in output
    assert '"name": "read_file"' in output
    assert '"required": [' in output


def test_cli_tools_can_disable_toolsets(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))

    assert main(["tools", "--disable-toolset", "files"]) == 0

    output = capsys.readouterr().out
    assert "echo\tcore\tavailable" in output
    assert "read_file" not in output


def test_cli_lists_sessions(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))
    main(["chat", "hello"])
    capsys.readouterr()

    assert main(["sessions"]) == 0

    output = capsys.readouterr().out
    assert "hello" in output
    assert "messages" in output


def test_cli_searches_sessions(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))
    main(["chat", "searchable", "phrase"])
    capsys.readouterr()

    assert main(["search", "searchable"]) == 0

    output = capsys.readouterr().out
    assert "searchable phrase" in output


def test_cli_shows_resolved_config_without_secret(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))
    (tmp_path / "config.yaml").write_text(
        "model: test/model\n"
        "api_key: secret-value\n"
        "max_iterations: 3\n"
    )

    assert main(["config"]) == 0

    output = capsys.readouterr().out
    assert f"home: {tmp_path}" in output
    assert "model: test/model" in output
    assert "api_key: <set>" in output
    assert "secret-value" not in output
    assert "max_iterations: 3" in output
    assert "enabled_toolsets: core, files" in output


def test_cli_shows_session_messages(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))
    main(["chat", "hello"])
    output = capsys.readouterr().out
    session_id = output.split("[session: ", 1)[1].split("]", 1)[0]

    assert main(["show", session_id]) == 0

    output = capsys.readouterr().out
    assert "1. system" in output
    assert "2. user" in output
    assert "hello" in output
    assert "3. assistant" in output
    assert "[local/echo] hello" in output


def test_cli_shows_session_messages_as_json(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))
    main(["chat", "hello"])
    output = capsys.readouterr().out
    session_id = output.split("[session: ", 1)[1].split("]", 1)[0]

    assert main(["show", session_id, "--json"]) == 0

    output = capsys.readouterr().out
    assert '"role": "user"' in output
    assert '"content": "hello"' in output


def test_cli_writes_log_file(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))

    assert main(["chat", "hello"]) == 0
    capsys.readouterr()

    log_path = tmp_path / "logs" / "agent.log"
    assert log_path.exists()
    assert "chat command completed" in log_path.read_text()
