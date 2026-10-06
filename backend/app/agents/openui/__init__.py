"""OpenUI Lang for pages: the generated prompts and a small parser.

The prompts and the spec next to this file are generated from the frontend's page catalogue
(`frontend/src/lib/openui/catalog.js`) with `npm run page-prompt`; do not edit them by hand.

The parser covers what the page catalogue uses: statements (`id = Expr`), component calls,
strings, numbers, booleans, null, arrays, objects and references. State, queries and
built-ins are off in the page prompt, so they parse to `None`.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

HERE = Path(__file__).parent
ROOT = "Page"


@lru_cache
def gateway_prompt() -> str:
    """The `cloud: true` configuration block the OpenUI Gateway builds the prompt from."""
    return (HERE / "page.gateway.txt").read_text(encoding="utf-8").strip()


@lru_cache
def full_prompt() -> str:
    """The whole prompt, for a model called directly instead of through the Gateway."""
    return (HERE / "page.txt").read_text(encoding="utf-8").strip()


@lru_cache
def _spec() -> dict[str, Any]:
    return json.loads((HERE / "page.spec.json").read_text(encoding="utf-8"))


@lru_cache
def component_names() -> frozenset[str]:
    return frozenset(_spec()["components"])


class ParseError(ValueError):
    pass


@dataclass
class Node:
    """A component call: its name and positional arguments."""

    name: str
    args: list[Any] = field(default_factory=list)


@dataclass
class Ref:
    name: str


_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
_NUMBER = re.compile(r"-?\d+(\.\d+)?([eE][+-]?\d+)?")
_FENCE = re.compile(r"```[A-Za-z0-9_-]*\s*\n(.*?)```", re.S)


def strip_fence(text: str) -> str:
    """Models sometimes wrap the answer in a code fence; the source is what is inside."""
    match = _FENCE.search(text)
    return (match.group(1) if match else text).strip()


class _Parser:
    def __init__(self, text: str) -> None:
        self.text = text
        self.pos = 0

    # -- low level ---------------------------------------------------------

    def _skip(self, newlines: bool = True) -> None:
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char in " \t\r" or (newlines and char == "\n"):
                self.pos += 1
            elif self.text.startswith("//", self.pos):
                end = self.text.find("\n", self.pos)
                self.pos = len(self.text) if end == -1 else end
            else:
                break

    def _peek(self) -> str:
        return self.text[self.pos] if self.pos < len(self.text) else ""

    def _expect(self, char: str) -> None:
        self._skip()
        if self._peek() != char:
            raise ParseError(f"expected {char!r} at {self.pos}")
        self.pos += 1

    def _ident(self) -> str:
        match = _IDENT.match(self.text, self.pos)
        if not match:
            raise ParseError(f"expected a name at {self.pos}")
        self.pos = match.end()
        return match.group(0)

    # -- grammar -----------------------------------------------------------

    def statements(self) -> list[tuple[str, Any]]:
        out: list[tuple[str, Any]] = []
        # Where each statement starts, so a problem can name its line.
        self.starts: list[int] = []
        self._skip()
        while self.pos < len(self.text):
            self.starts.append(self.pos)
            if self._peek() == "$":  # a state declaration; not used by pages
                self.pos += 1
            name = self._ident()
            self._expect("=")
            out.append((name, self.expr()))
            self._skip()
        return out

    def expr(self) -> Any:
        self._skip()
        char = self._peek()
        if char in "\"'":
            return self._string(char)
        if char == "[":
            return self._list("[", "]")
        if char == "{":
            return self._object()
        if char == "$":
            self.pos += 1
            self._ident()
            return None
        if char == "@":
            self.pos += 1
            self._ident()
            if self._peek() == "(":
                self._list("(", ")")
            return None
        number = _NUMBER.match(self.text, self.pos)
        if number:
            self.pos = number.end()
            value = number.group(0)
            return float(value) if any(c in value for c in ".eE") else int(value)
        name = self._ident()
        if name in ("true", "false"):
            return name == "true"
        if name == "null":
            return None
        if self._peek() == "(":
            return Node(name, self._list("(", ")"))
        while self._peek() == ".":  # member access, only meaningful with queries
            self.pos += 1
            self._ident()
        return Ref(name)

    def _string(self, quote: str) -> str:
        start = self.pos
        self.pos += 1
        while self.pos < len(self.text):
            char = self.text[self.pos]
            if char == "\\":
                self.pos += 2
                continue
            if char == quote:
                self.pos += 1
                raw = self.text[start + 1 : self.pos - 1]
                return _unescape(raw)
            self.pos += 1
        raise ParseError("unterminated string")

    def _list(self, open_: str, close: str) -> list[Any]:
        self._expect(open_)
        items: list[Any] = []
        self._skip()
        if self._peek() == close:
            self.pos += 1
            return items
        while True:
            items.append(self.expr())
            self._skip()
            char = self._peek()
            if char == ",":
                self.pos += 1
                self._skip()
                if self._peek() == close:  # trailing comma
                    self.pos += 1
                    return items
                continue
            if char == close:
                self.pos += 1
                return items
            raise ParseError(f"expected ',' or {close!r} at {self.pos}")

    def _object(self) -> dict[str, Any]:
        self._expect("{")
        out: dict[str, Any] = {}
        self._skip()
        if self._peek() == "}":
            self.pos += 1
            return out
        while True:
            self._skip()
            key = self._string(self._peek()) if self._peek() in "\"'" else self._ident()
            self._expect(":")
            out[key] = self.expr()
            self._skip()
            char = self._peek()
            self.pos += 1
            if char == "}":
                return out
            if char != ",":
                raise ParseError(f"expected ',' or '}}' at {self.pos}")


def _unescape(raw: str) -> str:
    try:
        return json.loads(f'"{raw}"')
    except json.JSONDecodeError:
        # Raw newlines or a lone backslash: keep the text and decode what is standard.
        return (
            raw.replace("\\n", "\n")
            .replace("\\t", "\t")
            .replace('\\"', '"')
            .replace("\\'", "'")
            .replace("\\\\", "\\")
        )


def parse(source: str) -> Node:
    """Parse a page and return its root, with every reference resolved.

    Raises `ParseError` when the source does not parse or its root is not a Page.
    """
    statements = _Parser(strip_fence(source)).statements()
    if not statements:
        raise ParseError("empty source")
    table = dict(statements)
    root = table.get("root", statements[0][1])

    def resolve(value: Any, seen: frozenset[str]) -> Any:
        if isinstance(value, Ref):
            if value.name in seen or value.name not in table:
                return None
            return resolve(table[value.name], seen | {value.name})
        if isinstance(value, Node):
            return Node(value.name, [resolve(arg, seen) for arg in value.args])
        if isinstance(value, list):
            return [resolve(item, seen) for item in value]
        if isinstance(value, dict):
            return {key: resolve(item, seen) for key, item in value.items()}
        return value

    root = resolve(root, frozenset({"root"}))
    if not isinstance(root, Node) or root.name != ROOT:
        raise ParseError("the root is not a Page")
    return root


def statements(source: str) -> list[tuple[str, Any]]:
    """The source's statements in order, as `(name, expression)`, references left unresolved."""
    return _Parser(strip_fence(source)).statements()


def _dump(value: Any) -> str:
    if isinstance(value, Node):
        args = list(value.args)
        while args and args[-1] is None:  # optional arguments are left out from the end
            args.pop()
        return f"{value.name}({', '.join(_dump(arg) for arg in args)})"
    if isinstance(value, Ref):
        return value.name
    if isinstance(value, list):
        return f"[{', '.join(_dump(item) for item in value)}]"
    if isinstance(value, dict):
        return "{" + ", ".join(f"{json.dumps(k)}: {_dump(v)}" for k, v in value.items()) + "}"
    if value is None or isinstance(value, (bool, int, float, str)):
        return json.dumps(value, ensure_ascii=False)
    raise TypeError(f"cannot write {type(value).__name__} as OpenUI Lang")


def dump(statements: list[tuple[str, Any]]) -> str:
    """Write statements back as OpenUI Lang, one per line."""
    return "\n".join(f"{name} = {_dump(expr)}" for name, expr in statements)


def unknown_components(root: Node) -> set[str]:
    """Component names in the page that are not in the catalogue."""
    found: set[str] = set()
    known = component_names()

    def walk(value: Any) -> None:
        if isinstance(value, Node):
            if value.name not in known:
                found.add(value.name)
            for arg in value.args:
                walk(arg)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(root)
    return found


# -- checking a page against the catalogue ------------------------------------------------------

# Past this many, a model fixes those first and sends the page again.
MAX_PROBLEMS = 12
_AT = re.compile(r" at (\d+)$")


def _line(text: str, pos: int) -> int:
    return text.count("\n", 0, pos) + 1


def _describe(value: Any) -> str:
    if isinstance(value, Node):
        return f"{value.name}(...)"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return "a number"
    if isinstance(value, str):
        return "a string"
    if isinstance(value, list):
        return "a list"
    if isinstance(value, dict):
        return "an object"
    return "null"


def _types(schema: dict[str, Any]) -> list[str]:
    kind = schema.get("type")
    return kind if isinstance(kind, list) else [kind] if kind else []


def _fits(value: Any, kind: str) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if kind == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if kind == "boolean":
        return isinstance(value, bool)
    if kind == "array":
        return isinstance(value, list)
    if kind == "object":
        return isinstance(value, dict)
    if kind == "null":
        return value is None
    return True


def _ref_name(schema: dict[str, Any]) -> str | None:
    ref = schema.get("$ref", "")
    return ref.rsplit("/", 1)[-1] if ref.startswith("#/$defs/") else None


class _Checker:
    """Walks a page's statements against the catalogue's schema (`page.spec.json`, generated from
    the frontend's), matching each call's arguments to its props in order."""

    def __init__(self, table: dict[str, Any], lines: dict[str, int]) -> None:
        self.defs: dict[str, Any] = _spec()["schema"]["$defs"]
        self.signatures = {name: c["signature"] for name, c in _spec()["components"].items()}
        self.table = table
        self.lines = lines
        self.found: list[str] = []

    def problem(self, line: int, text: str) -> None:
        message = f"Line {line}: {text}"
        if message not in self.found:
            self.found.append(message)

    def node(self, node: Node, line: int) -> None:
        schema = self.defs.get(node.name)
        if schema is None:
            known = ", ".join(sorted(self.defs))
            self.problem(line, f"{node.name} is not in the catalogue. The components are: {known}.")
            return
        props = list(schema.get("properties", {}).items())
        required = set(schema.get("required", []))
        signature = self.signatures.get(node.name, node.name)
        if len(node.args) > len(props):
            self.problem(
                line, f"{node.name} takes at most {len(props)} arguments, got {len(node.args)}: {signature}."
            )
        for index, (prop, prop_schema) in enumerate(props):
            value = node.args[index] if index < len(node.args) else None
            if value is None:
                if prop in required:
                    self.problem(line, f"{node.name} needs its {prop}: {signature}.")
                continue
            self.value(value, prop_schema, f"{node.name}'s {prop}", line, signature)

    def value(self, value: Any, schema: dict[str, Any], where: str, line: int, signature: str) -> None:
        # A reference to another statement: that line is checked on its own, so only its
        # component's name matters here.
        shallow = False
        if isinstance(value, Ref):
            if value.name not in self.table:
                self.problem(line, f"{value.name} is used but never defined.")
                return
            target = self.table[value.name]
            if isinstance(target, Ref):
                return
            shallow = isinstance(target, Node)
            line = line if shallow else self.lines.get(value.name, line)
            value = target

        expected = _ref_name(schema)
        if expected:
            if not (isinstance(value, Node) and value.name == expected):
                self.problem(line, f"{where} must be a {expected}(...), not {_describe(value)}: {signature}.")
            elif not shallow:
                self.node(value, line)
            return

        if "anyOf" in schema:
            options = schema["anyOf"]
            names = [n for n in (_ref_name(o) for o in options) if n]
            if isinstance(value, Node) and value.name in names:
                if not shallow:
                    self.node(value, line)
                return
            if names and isinstance(value, Node):
                self.problem(line, f"{where} can't hold {value.name}; it takes {', '.join(names)}.")
                return
            for option in (o for o in options if not _ref_name(o)):
                trial = _Checker(self.table, self.lines)
                trial.value(value, option, where, line, signature)
                if not trial.found:
                    return
            self.problem(line, f"{where} doesn't take {_describe(value)}: {signature}.")
            return

        if isinstance(value, Node):
            self.problem(line, f"{where} takes a plain value here, not {value.name}(...): {signature}.")
            return
        kinds = _types(schema)
        if kinds and not any(_fits(value, kind) for kind in kinds):
            self.problem(line, f"{where} must be {' or '.join(kinds)}, not {_describe(value)}: {signature}.")
            return
        if "enum" in schema and value not in schema["enum"]:
            options = ", ".join(json.dumps(option) for option in schema["enum"])
            self.problem(line, f"{where} must be one of {options}, not {json.dumps(value)}.")
            return
        if isinstance(value, list) and "items" in schema:
            for index, item in enumerate(value):
                self.value(item, schema["items"], f"{where}, item {index + 1}", line, signature)
        if isinstance(value, dict):
            props = schema.get("properties", {})
            for key in schema.get("required", []):
                if value.get(key) is None:
                    self.problem(line, f"{where} needs its {key!r}.")
            for key, item in value.items():
                if key in props:
                    if item is not None:
                        self.value(item, props[key], f"{where}'s {key!r}", line, signature)
                elif schema.get("additionalProperties") is False:
                    allowed = ", ".join(props) or "none"
                    self.problem(line, f"{where} has no {key!r}; it takes: {allowed}.")


def _uses(value: Any, out: set[str]) -> None:
    if isinstance(value, Ref):
        out.add(value.name)
    elif isinstance(value, Node):
        for arg in value.args:
            _uses(arg, out)
    elif isinstance(value, list):
        for item in value:
            _uses(item, out)
    elif isinstance(value, dict):
        for item in value.values():
            _uses(item, out)


def problems(source: str) -> list[str]:
    """What stops `source` from being a page the catalogue can draw, each saying where and what to
    change; empty when nothing does. Stricter than `parse`, which a model's page goes through: a
    page that comes in as written has no web agent behind it to fall back on."""
    empty = "The page is empty: write root = Page([...]) with at least one block."
    text = strip_fence(source)
    if not text:
        return [empty]
    parser = _Parser(text)
    try:
        found = parser.statements()
    except ParseError as exc:
        message = _AT.sub("", str(exc))
        return [f"Line {_line(text, parser.pos)}: it doesn't parse ({message})."]
    if not found:  # only comments
        return [empty]

    table: dict[str, Any] = {}
    lines: dict[str, int] = {}
    out: list[str] = []
    for (name, expr), start in zip(found, parser.starts):
        line = _line(text, start)
        if name in table:
            out.append(f"Line {line}: {name} is already defined on line {lines[name]}; give it another name.")
            continue
        table[name] = expr
        lines[name] = line

    root_name = "root" if "root" in table else found[0][0]
    root = table[root_name]
    if not (isinstance(root, Node) and root.name == ROOT):
        return out + [f"Line {lines[root_name]}: the page must start with root = Page([...]), not {_describe(root)}."]
    blocks = root.args[0] if root.args else None
    if isinstance(blocks, list) and not blocks:
        out.append(f"Line {lines[root_name]}: the page has no blocks; a blank page isn't saved.")

    checker = _Checker(table, lines)
    for name, expr in table.items():
        if isinstance(expr, Node):
            checker.node(expr, lines[name])
    out += checker.found

    # Only what the root reaches is drawn: a statement nothing uses would be silently dropped.
    reached: set[str] = {root_name}
    pending = [root_name]
    while pending:
        used: set[str] = set()
        _uses(table[pending.pop()], used)
        for name in used - reached:
            if name in table:
                reached.add(name)
                pending.append(name)
    for name in table:
        if name not in reached:
            out.append(f"Line {lines[name]}: {name} is never used, so it won't show; put it in its parent's list, or remove it.")

    return out[:MAX_PROBLEMS]
