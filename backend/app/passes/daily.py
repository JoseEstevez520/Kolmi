from __future__ import annotations

from typing import Any

from ..agents import LLM, build_page, get_llm, get_web_llm, run_gatekeeper
from ..agents.schemas import Batch, GatekeeperResult, NewPage
from ..store import Store, SupabaseStore

STALE_MINUTES = 120


def _model_name(llm: LLM) -> str:
    return getattr(llm, "model", None) or "unknown"


def _review(plan: GatekeeperResult, note_ids: set[int]) -> list[int]:
    """Notes the gatekeeper neither routed nor discarded."""
    mentioned = {nid for batch in plan.batches for nid in batch.note_ids}
    mentioned |= {item.note_id for item in plan.discarded}
    return sorted(note_ids - mentioned)


def _resolve_target(
    store: Store, pass_id: int, batch: Batch, stats: dict[str, Any]
) -> dict[str, Any] | None:
    """Find the page a batch goes to, creating it when the gatekeeper asked."""
    if batch.action == "update" and batch.node_id is not None:
        page = store.page(batch.node_id)
        if page:
            return page
        stats["flagged"].append(
            {"node_id": batch.node_id, "reason": "gatekeeper chose a page that does not exist"}
        )
        store.log(
            pass_id=pass_id,
            note_id=None,
            node_id=batch.node_id,
            action="flagged",
            reason="Page not found",
        )
        return None

    new = batch.new_page or NewPage(parent_id=None, title="Untitled")
    created = store.create_page(
        parent_id=new.parent_id, title=new.title, description=new.description
    )
    store.log(
        pass_id=pass_id,
        note_id=None,
        node_id=created["id"],
        action="created",
        reason=batch.reason,
    )
    stats["created"] += 1
    return {"id": created["id"], "title": new.title, "content_md": "", "content_web": ""}


def _write_batch(
    store: Store,
    llm: LLM,
    web_llm: LLM | None,
    pass_id: int,
    batch: Batch,
    page: dict[str, Any],
    stats: dict[str, Any],
) -> None:
    existing_md = page.get("content_md") or ""
    existing_web = page.get("content_web") or ""

    written = build_page(
        llm,
        web_llm,
        title=page["title"],
        summary=batch.summary,
        existing_md=existing_md,
        existing_web=existing_web,
    )

    if existing_md.strip() or existing_web.strip():
        store.save_version(page["id"], existing_md, existing_web)

    store.write_page(
        page["id"], content_md=written.content_md, content_web=written.content_web
    )

    if web_llm is not None and written.source != "web":
        stats["web_fallbacks"].append(
            {"node_id": page["id"], "reason": written.fallback_reason}
        )

    if batch.action == "update":
        store.log(
            pass_id=pass_id,
            note_id=None,
            node_id=page["id"],
            action="updated",
            reason=batch.reason,
        )
        stats["updated"] += 1

    stats["pages"].append(
        {"node_id": page["id"], "title": page["title"], "format": written.source}
    )


def _apply(
    store: Store,
    llm: LLM,
    web_llm: LLM | None,
    pass_id: int,
    plan: GatekeeperResult,
    note_ids: set[int],
    stats: dict[str, Any],
) -> None:
    for batch in plan.batches:
        page = _resolve_target(store, pass_id, batch, stats)
        if page is None:
            continue
        _write_batch(store, llm, web_llm, pass_id, batch, page, stats)
        for note_id in batch.note_ids:
            if note_id in note_ids:
                store.set_note_status(note_id, "processed")

    for item in plan.discarded:
        if item.note_id not in note_ids:
            continue
        store.set_note_status(item.note_id, "discarded")
        store.log(
            pass_id=pass_id,
            note_id=item.note_id,
            node_id=None,
            action="discarded",
            reason=item.reason,
        )
        stats["discarded"] += 1

    for note_id in _review(plan, note_ids):
        store.log(
            pass_id=pass_id,
            note_id=note_id,
            node_id=None,
            action="flagged",
            reason="The gatekeeper did not review this note; left pending.",
        )


def run_daily_pass(
    *,
    store: Store | None = None,
    llm: LLM | None = None,
    web_llm: LLM | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """One pass: read the pending notes and turn them into pages.

    Returns a summary. With `dry_run` it only asks the gatekeeper what it would
    do, and writes nothing (and spends no tokens beyond that one call).

    `llm` runs the gatekeeper and the Markdown fallback; `web_llm` writes the
    pages as OpenUI Lang. With neither given, both come from the settings. When
    `llm` is given and `web_llm` is not, pages are written as Markdown only.
    """
    store = store or SupabaseStore()
    if llm is None:
        llm = get_llm()
        web_llm = web_llm or get_web_llm()

    running = store.running_pass(STALE_MINUTES)
    if running:
        return {"status": "skipped", "reason": f"pass {running['id']} is still running"}

    notes = store.pending_notes()
    if not notes:
        return {"status": "empty", "notes": 0}

    note_ids = {note["id"] for note in notes}
    nodes = store.nodes()

    if dry_run:
        plan = run_gatekeeper(llm, notes, nodes)
        return {
            "status": "dry-run",
            "model": _model_name(llm),
            "web_model": _model_name(web_llm) if web_llm is not None else None,
            "notes": len(notes),
            "batches": [batch.model_dump() for batch in plan.batches],
            "discarded": [item.model_dump() for item in plan.discarded],
            "unreviewed": _review(plan, note_ids),
        }

    stats: dict[str, Any] = {
        "notes": len(notes),
        "batches": 0,
        "created": 0,
        "updated": 0,
        "discarded": 0,
        "pages": [],
        "flagged": [],
        "web_model": _model_name(web_llm) if web_llm is not None else None,
        "web_fallbacks": [],
    }

    pass_id = store.open_pass(_model_name(llm))
    try:
        plan = run_gatekeeper(llm, notes, nodes)
        stats["batches"] = len(plan.batches)
        stats["unreviewed"] = _review(plan, note_ids)
        _apply(store, llm, web_llm, pass_id, plan, note_ids, stats)
        store.close_pass(pass_id, status="done", stats=stats)
    except Exception as exc:
        store.close_pass(pass_id, status="failed", stats=stats, error=str(exc))
        raise

    stats["status"] = "done"
    stats["pass_id"] = pass_id
    return stats


if __name__ == "__main__":
    from .__main__ import main

    main()
