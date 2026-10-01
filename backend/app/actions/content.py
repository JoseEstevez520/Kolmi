from fastapi import HTTPException
from pydantic import BaseModel

from ..auth import Context
from .registry import action


class ViewSectionParams(BaseModel):
    section_id: int


class ViewPageParams(BaseModel):
    page_id: int


class CreateModuleParams(BaseModel):
    name: str


class RenameModuleParams(BaseModel):
    module_id: int
    name: str


class ModuleIdParams(BaseModel):
    module_id: int


class CreateSectionParams(BaseModel):
    module_id: int
    name: str


class RenameSectionParams(BaseModel):
    section_id: int
    name: str


class SectionIdParams(BaseModel):
    section_id: int


class CreatePageParams(BaseModel):
    section_id: int
    title: str


class RenamePageParams(BaseModel):
    page_id: int
    title: str


class PageIdParams(BaseModel):
    page_id: int


class ReorderParams(BaseModel):
    ids: list[int]


def _next_position(client, table: str, **filters) -> int:
    query = (
        client.table(table).select("position").order("position", desc=True).limit(1)
    )
    for column, value in filters.items():
        query = query.eq(column, value)
    rows = query.execute().data
    return rows[0]["position"] + 1 if rows else 0


@action(
    name="list_modules",
    description="List the content structure: modules with their sections nested.",
    method="GET",
    path="/modules",
)
def list_modules(ctx: Context, params: None):
    return (
        ctx.client.table("modules")
        .select("*, sections(*)")
        .order("position")
        .order("position", foreign_table="sections")
        .execute()
        .data
    )


@action(
    name="view_section",
    description="Get a section with its pages (id and title).",
    params=ViewSectionParams,
    method="GET",
    path="/section",
)
def view_section(ctx: Context, params: ViewSectionParams):
    rows = (
        ctx.client.table("sections")
        .select("*, pages(id, title)")
        .eq("id", params.section_id)
        .order("position", foreign_table="pages")
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, "Section not found")
    return rows[0]


@action(
    name="view_page",
    description="Get a page with its Markdown and web content.",
    params=ViewPageParams,
    method="GET",
    path="/page",
)
def view_page(ctx: Context, params: ViewPageParams):
    rows = (
        ctx.client.table("pages")
        .select("id, section_id, title, content_md, content_web")
        .eq("id", params.page_id)
        .limit(1)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, "Page not found")
    return rows[0]


@action(
    name="create_module",
    description="Create a module at the end of the list.",
    params=CreateModuleParams,
    path="/module",
    min_role="admin",
)
def create_module(ctx: Context, params: CreateModuleParams):
    row = {"name": params.name, "position": _next_position(ctx.client, "modules")}
    return ctx.client.table("modules").insert(row).execute().data[0]


@action(
    name="rename_module",
    description="Rename a module.",
    params=RenameModuleParams,
    path="/module/rename",
    min_role="admin",
)
def rename_module(ctx: Context, params: RenameModuleParams):
    rows = (
        ctx.client.table("modules")
        .update({"name": params.name})
        .eq("id", params.module_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, "Module not found")
    return rows[0]


@action(
    name="reorder_modules",
    description="Set the order of modules to the given list of ids.",
    params=ReorderParams,
    path="/module/reorder",
    min_role="admin",
)
def reorder_modules(ctx: Context, params: ReorderParams):
    for index, module_id in enumerate(params.ids):
        ctx.client.table("modules").update({"position": index}).eq(
            "id", module_id
        ).execute()
    return {"ok": True}


@action(
    name="delete_module",
    description="Delete a module and everything under it.",
    params=ModuleIdParams,
    path="/module/delete",
    requires_confirmation=True,
    min_role="admin",
)
def delete_module(ctx: Context, params: ModuleIdParams):
    rows = (
        ctx.client.table("modules").delete().eq("id", params.module_id).execute().data
    )
    if not rows:
        raise HTTPException(404, "Module not found")
    return {"ok": True}


@action(
    name="create_section",
    description="Create a section at the end of a module.",
    params=CreateSectionParams,
    path="/section",
    min_role="admin",
)
def create_section(ctx: Context, params: CreateSectionParams):
    row = {
        "module_id": params.module_id,
        "name": params.name,
        "position": _next_position(
            ctx.client, "sections", module_id=params.module_id
        ),
    }
    return ctx.client.table("sections").insert(row).execute().data[0]


@action(
    name="rename_section",
    description="Rename a section.",
    params=RenameSectionParams,
    path="/section/rename",
    min_role="admin",
)
def rename_section(ctx: Context, params: RenameSectionParams):
    rows = (
        ctx.client.table("sections")
        .update({"name": params.name})
        .eq("id", params.section_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, "Section not found")
    return rows[0]


@action(
    name="reorder_sections",
    description="Set the order of sections to the given list of ids.",
    params=ReorderParams,
    path="/section/reorder",
    min_role="admin",
)
def reorder_sections(ctx: Context, params: ReorderParams):
    for index, section_id in enumerate(params.ids):
        ctx.client.table("sections").update({"position": index}).eq(
            "id", section_id
        ).execute()
    return {"ok": True}


@action(
    name="delete_section",
    description="Delete a section and everything under it.",
    params=SectionIdParams,
    path="/section/delete",
    requires_confirmation=True,
    min_role="admin",
)
def delete_section(ctx: Context, params: SectionIdParams):
    rows = (
        ctx.client.table("sections").delete().eq("id", params.section_id).execute().data
    )
    if not rows:
        raise HTTPException(404, "Section not found")
    return {"ok": True}


@action(
    name="create_page",
    description="Create a page at the end of a section.",
    params=CreatePageParams,
    path="/page",
    min_role="admin",
)
def create_page(ctx: Context, params: CreatePageParams):
    row = {
        "section_id": params.section_id,
        "title": params.title,
        "position": _next_position(
            ctx.client, "pages", section_id=params.section_id
        ),
    }
    return ctx.client.table("pages").insert(row).execute().data[0]


@action(
    name="rename_page",
    description="Rename a page.",
    params=RenamePageParams,
    path="/page/rename",
    min_role="admin",
)
def rename_page(ctx: Context, params: RenamePageParams):
    rows = (
        ctx.client.table("pages")
        .update({"title": params.title})
        .eq("id", params.page_id)
        .execute()
        .data
    )
    if not rows:
        raise HTTPException(404, "Page not found")
    return rows[0]


@action(
    name="reorder_pages",
    description="Set the order of pages to the given list of ids.",
    params=ReorderParams,
    path="/page/reorder",
    min_role="admin",
)
def reorder_pages(ctx: Context, params: ReorderParams):
    for index, page_id in enumerate(params.ids):
        ctx.client.table("pages").update({"position": index}).eq(
            "id", page_id
        ).execute()
    return {"ok": True}


@action(
    name="delete_page",
    description="Delete a page.",
    params=PageIdParams,
    path="/page/delete",
    requires_confirmation=True,
    min_role="admin",
)
def delete_page(ctx: Context, params: PageIdParams):
    rows = ctx.client.table("pages").delete().eq("id", params.page_id).execute().data
    if not rows:
        raise HTTPException(404, "Page not found")
    return {"ok": True}
