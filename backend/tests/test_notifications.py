from datetime import datetime, timezone

from app.actions import get_action, invoke
from tests.test_chat_tools import _Client, _ctx


def test_feed_has_shared_page_updates_and_only_replies_to_participated_threads(monkeypatch):
    client = _Client()
    now = datetime.now(timezone.utc).isoformat()
    client.rows("ai_passes").append(dict(id=1, status="done", started_at=now, stats={"pages": [{"node_id": 20}], "private_note": "never expose"}))
    client.rows("nodes").clear()
    client.rows("nodes").append(dict(id=20, title="Shared page", kind="page", updated_at=now))
    client.rows("forum_threads").append(dict(id=1, author_id="u1"))
    client.rows("forum_posts").extend([
        dict(id=1, thread_id=1, author_id="other", created_at=now),
        dict(id=2, thread_id=2, author_id="other", created_at=now),
        dict(id=3, thread_id=1, author_id="u1", created_at=now),
    ])
    monkeypatch.setattr("app.actions.notifications.read_settings", lambda _: {"forum_enabled": True})
    result = invoke(get_action("my_notifications"), _ctx(client), {})
    assert {item["id"] for item in result["items"]} == {"page:20", "reply:1"}
    assert result["digest"] == {"passes": 1, "pages": 1}
    assert "never expose" not in str(result)
