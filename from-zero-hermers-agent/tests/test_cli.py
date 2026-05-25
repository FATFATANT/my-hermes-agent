from hermers_agent.cli import main


def test_cli_chat_saves_session(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("HERMERS_HOME", str(tmp_path))

    assert main(["chat", "hello"]) == 0

    output = capsys.readouterr().out
    assert "[local/echo] hello" in output
    assert "[session:" in output


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
