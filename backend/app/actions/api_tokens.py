"""A member's own personal tokens, for their AI over the MCP: made, listed and revoked from the
web. No tool can reach them: an AI never makes or sees a token."""

from fastapi import HTTPException
from pydantic import BaseModel, Field, field_validator

from .. import tokens
from ..auth import Context
from .registry import action


class TokenNameParams(BaseModel):
    name: str = Field(..., min_length=1, max_length=60, description="What the token is for, such as the editor it goes in.")

    @field_validator("name")
    @classmethod
    def _trimmed(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("the name can't be blank")
        return value


class TokenIdParams(BaseModel):
    token_id: int = Field(..., description="The token's id, from list_my_tokens.")


@action(
    name="create_my_token",
    description="Make a personal token for your own AI. The answer is the only time the token itself is shown.",
    params=TokenNameParams,
    path="/tokens",
)
def create_my_token(ctx: Context, params: TokenNameParams):
    return tokens.create(ctx.client, ctx.user_id, params.name)


@action(
    name="list_my_tokens",
    read_only=True,
    description="Your personal tokens: each one's name, prefix, when it was made and last used, and whether it was revoked. Never the token itself.",
    method="GET",
    path="/tokens",
)
def list_my_tokens(ctx: Context, params: None):
    return tokens.listed(ctx.client, ctx.user_id)


@action(
    name="revoke_my_token",
    description="Revoke one of your personal tokens: the AI that holds it can do nothing more.",
    params=TokenIdParams,
    path="/tokens/revoke",
    requires_confirmation=True,
)
def revoke_my_token(ctx: Context, params: TokenIdParams):
    if not tokens.revoke(ctx.client, ctx.user_id, params.token_id):
        raise HTTPException(404, f"You have no live token {params.token_id}; list_my_tokens lists yours")
    return {"revoked": params.token_id}
