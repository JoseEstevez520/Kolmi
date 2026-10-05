import io
import zipfile

import pytest

from app.export import build, plan, rewrite, slugify, to_zip

NODES = [
    {"id": 1, "parent_id": None, "kind": "section", "title": "Módulos", "position": 0},
    {"id": 2, "parent_id": 1, "kind": "section", "title": "DWCS", "position": 0},
    {"id": 3, "parent_id": 2, "kind": "page", "title": "Servicios e inyección", "position": 1,
     "content_md": "# Servicios e inyección\n\nVer [Scopes y estado](scopes-y-estado.md) y [otra](/node/5).\n"},
    {"id": 4, "parent_id": 2, "kind": "page", "title": "Scopes y estado", "position": 0,
     "content_md": "Texto. Vuelve a [Servicios](/node/3#detalle).\n"},
    {"id": 5, "parent_id": 1, "kind": "page", "title": "Suelta", "position": 1, "content_md": "x"},
    {"id": 6, "parent_id": 1, "kind": "page", "title": "Vacía", "position": 2, "content_md": "  "},
    {"id": 7, "parent_id": None, "kind": "section", "title": "Sin páginas", "position": 1},
]


def test_slugify_strips_accents_and_symbols():
    assert slugify("Spring, Spring Boot y el contenedor") == "spring-spring-boot-y-el-contenedor"
    assert slugify("¿Qué es la IA?") == "que-es-la-ia"
    assert slugify("???", "9") == "9"


def test_plan_mirrors_the_tree_in_the_admins_order_and_skips_empty():
    layout = {i: path for i, (path, _) in plan(NODES).items()}
    assert layout == {
        4: "01-modulos/01-dwcs/01-scopes-y-estado.md",
        3: "01-modulos/01-dwcs/02-servicios-e-inyeccion.md",
        5: "01-modulos/02-suelta.md",
    }


def test_plan_scope_starts_at_the_section_and_keeps_the_trail():
    layout = plan(NODES, 2)
    assert layout[4] == ("01-scopes-y-estado.md", [])
    assert plan(NODES)[4][1] == ["Módulos", "DWCS"]


def test_plan_unknown_scope():
    with pytest.raises(KeyError):
        plan(NODES, 99)


def test_links_to_pages_in_the_export_become_relative_files():
    files = build(NODES)
    text = files["01-modulos/01-dwcs/02-servicios-e-inyeccion.md"]
    assert "[Scopes y estado](01-scopes-y-estado.md)" in text  # matched by its title
    assert "[otra](../02-suelta.md)" in text  # /node/5
    assert files["01-modulos/01-dwcs/01-scopes-y-estado.md"].count("[Servicios](02-servicios-e-inyeccion.md)") == 1


def test_links_that_lead_nowhere_become_plain_text():
    out = rewrite("a [fundamentos](../fundamentos/) b [x](/node/99) c [web](https://x.org) d [s](#s)",
                  "a.md", {}, {})
    assert out == "a fundamentos b x c [web](https://x.org) d [s](#s)"


def test_images_keep_external_urls_and_lose_the_missing_files():
    out = rewrite("![gráfica](benchmark.svg) ![logo](https://x.org/a.png)", "a.md", {}, {})
    assert out == "gráfica ![logo](https://x.org/a.png)"


def test_code_blocks_are_left_as_written():
    md = "```js\nconst a = [1](2)\n```\n[x](/node/1)"
    assert rewrite(md, "a.md", {}, {}) == "```js\nconst a = [1](2)\n```\nx"


def test_page_starts_with_title_and_where_it_sits_without_repeating_the_heading():
    text = build(NODES)["01-modulos/01-dwcs/02-servicios-e-inyeccion.md"]
    assert text.startswith("# Servicios e inyección\n\nMódulos > DWCS\n\n")
    assert text.count("# Servicios e inyección") == 1


def test_zip_holds_every_file():
    data = to_zip(build(NODES, 2))
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        assert archive.namelist() == ["01-scopes-y-estado.md", "02-servicios-e-inyeccion.md"]


# --- the route -------------------------------------------------------------------------------

from fastapi.testclient import TestClient  # noqa: E402

from app.auth import Context, get_context  # noqa: E402
from app.main import app  # noqa: E402


class _Nodes:
    def select(self, *_):
        return self

    def execute(self):
        return type("R", (), {"data": NODES})()


class _Client:
    def table(self, name):
        assert name == "nodes"
        return _Nodes()


def _as(approved=True):
    app.dependency_overrides[get_context] = lambda: Context(
        user_id="u1", email=None, profile={"approved": approved, "role": "student"}, client=_Client()
    )
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def test_route_returns_a_zip_for_a_member():
    r = _as().get("/export")
    assert r.status_code == 200 and r.headers["content-type"] == "application/zip"
    assert r.headers["content-disposition"] == 'attachment; filename="kolmi.zip"'
    assert len(zipfile.ZipFile(io.BytesIO(r.content)).namelist()) == 3


def test_route_scoped_to_a_section_is_named_after_it():
    r = _as().get("/export", params={"node_id": 2})
    assert r.headers["content-disposition"] == 'attachment; filename="kolmi-dwcs.zip"'
    assert len(zipfile.ZipFile(io.BytesIO(r.content)).namelist()) == 2


def test_route_refuses_an_unapproved_profile_and_unknown_or_empty_scopes():
    assert _as(approved=False).get("/export").status_code == 403
    assert _as().get("/export", params={"node_id": 99}).status_code == 404
    assert _as().get("/export", params={"node_id": 7}).status_code == 404  # a section with no pages
