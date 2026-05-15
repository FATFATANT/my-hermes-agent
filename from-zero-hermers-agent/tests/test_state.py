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


def test_session_store_searches_titles_and_messages(tmp_path):
    store = SessionStore(tmp_path / "sessions.sqlite3")
    title_match = store.create_session("alpha topic")
    body_match = store.create_session("ordinary title")

    store.append_messages(title_match, [{"role": "user", "content": "nothing special"}])
    store.append_messages(body_match, [{"role": "assistant", "content": "contains beta"}])

    title_results = store.search_sessions("alpha")
    body_results = store.search_sessions("beta")

    assert title_results[0].id == title_match
    assert body_results[0].id == body_match
    assert body_results[0].preview == "contains beta"
