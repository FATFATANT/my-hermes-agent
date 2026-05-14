from hermers_agent.llm import Message
from hermers_agent.state import SessionStore


def test_session_store_saves_and_lists_messages(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite3")
    session_id = store.create_session("hello")
    messages: list[Message] = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
    ]

    store.append_messages(session_id, messages)

    assert store.get_messages(session_id) == messages
    sessions = store.list_sessions()
    assert sessions[0].id == session_id
    assert sessions[0].title == "hello"
    assert sessions[0].message_count == 2
