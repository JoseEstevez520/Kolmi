from datetime import datetime, timezone

from app.actions import get_action, invoke
from tests.test_chat_tools import _Client, _ctx


def test_feed_has_shared_page_updates_without_exposing_private_pass_data():
    client = _Client()
    now = datetime.now(timezone.utc).isoformat()
    client.rows("ai_passes").append(dict(id=1, status="done", started_at=now, stats={"pages": [{"node_id": 20}], "private_note": "never expose"}))
    client.rows("nodes").clear()
    client.rows("nodes").append(dict(id=20, title="Shared page", kind="page", updated_at=now))
    result = invoke(get_action("my_notifications"), _ctx(client), {})
    assert {item["id"] for item in result["items"]} == {"page:20"}
    assert result["digest"] == {"passes": 1, "pages": 1}
    assert "never expose" not in str(result)
