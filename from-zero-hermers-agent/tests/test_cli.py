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
