"""The streaming chat: not an action, as its answer is a stream of events, not a return value."""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from .actions.chat import AskChatParams, stream_chat
from .auth import Context, get_context

router = APIRouter()


@router.post("/chat/stream")
def chat_stream(params: AskChatParams, ctx: Context = Depends(get_context)):
    return StreamingResponse(
        stream_chat(ctx, params),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
