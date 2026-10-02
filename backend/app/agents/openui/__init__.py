"""OpenUI Lang for pages: the generated prompts, a small parser and the Markdown view.

The prompts and the spec next to this file are generated from the frontend's page catalogue
(`frontend/src/lib/openui/catalog.js`) with `npm run page-prompt`; do not edit them by hand.

The parser covers what the page catalogue uses: statements (`id = Expr`), component calls,
strings, numbers, booleans, null, arrays, objects and references. State, queries and
built-ins are off in the page prompt, so they parse to `None`.
"""

from __future__ import annotations

import difflib
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
def component_names() -> frozenset[str]:
    spec = json.loads((HERE / "page.spec.json").read_text(encoding="utf-8"))
    return frozenset(spec["components"])


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
        self._skip()
        while self.pos < len(self.text):
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


# -- the Markdown view -----------------------------------------------------------------


def _arg(node: Node, index: int, default: Any = "") -> Any:
    value = node.args[index] if index < len(node.args) else None
    return default if value is None else value


def _quote(text: str) -> str:
    return "\n".join(f"> {line}" if line else ">" for line in text.splitlines())


def _children(node: Node) -> list[Node]:
    return [child for child in _arg(node, 0, []) if isinstance(child, Node)]


def _block(node: Any) -> str:
    if not isinstance(node, Node):
        return ""
    name = node.name
    if name == "Heading":
        level = 3 if _arg(node, 1, 2) == 3 else 2
        return f"{'#' * level} {_arg(node, 0)}"
    if name == "Text":
        return str(_arg(node, 0)).strip()
    if name == "CodeBlock":
        language, title = _arg(node, 1), _arg(node, 2)
        info = language + (f' title="{title}"' if title else "")
        return f"```{info}\n{str(_arg(node, 0)).rstrip()}\n```"
    if name == "Callout":
        kind, text, title = _arg(node, 0, "note"), _arg(node, 1), _arg(node, 2)
        body = (f"**{title}**\n\n" if title else "") + str(text).strip()
        return f"> [!{str(kind).upper()}]\n{_quote(body)}"
    if name == "Steps":
        lines = []
        for number, step in enumerate(_arg(node, 0, []), start=1):
            if not isinstance(step, Node):
                continue
            text = str(_arg(step, 1)).strip().replace("\n", "\n   ")
            lines.append(f"{number}. **{_arg(step, 0)}**" + (f"\n   {text}" if text else ""))
        return "\n".join(lines)
    if name == "CodeDiff":
        before, after, file = str(_arg(node, 0)), str(_arg(node, 1)), _arg(node, 2)
        lines = difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=3)
        body = "\n".join(line for line in lines if not line.startswith(("---", "+++", "@@")))
        info = "diff" + (f' title="{file}"' if file else "")
        return f"```{info}\n{body}\n```"
    if name == "Table":
        columns = [str(c) for c in _arg(node, 0, [])]
        if not columns:
            return ""
        rows = [list(row) if isinstance(row, list) else [] for row in _arg(node, 1, [])]

        def line(cells: list[Any]) -> str:
            return "| " + " | ".join(str(c or "").replace("|", "\\|").replace("\n", " ") for c in cells) + " |"

        table = [line(columns), line(["---"] * len(columns))]
        table += [line([row[i] if i < len(row) else "" for i in range(len(columns))]) for row in rows]
        caption = _arg(node, 2)
        return "\n".join(table) + (f"\n\n*{caption}*" if caption else "")
    if name == "DescriptionList":
        return "\n".join(
            f"- **{_arg(item, 0)}**: {str(_arg(item, 1)).strip()}"
            for item in _children(node)
        )
    if name == "Accordion":
        return "\n\n".join(
            f"**{_arg(item, 0)}**\n\n{str(_arg(item, 1)).strip()}" for item in _children(node)
        )
    if name == "Cards":
        lines = []
        for card in _children(node):
            title, text, href = _arg(card, 0), _arg(card, 1), _arg(card, 2)
            label = f"[{title}]({href})" if href else f"**{title}**"
            lines.append(f"- {label}" + (f": {text}" if text else ""))
        return "\n".join(lines)
    if name == "Logos":
        names = [str(n) for n in _arg(node, 0, [])]
        return ", ".join(names)
    if name == "TerminalReplay":
        lines = []
        for entry in _children(node):
            command, output, comment = _arg(entry, 0), _arg(entry, 1), _arg(entry, 2)
            if comment:
                lines.append(f"# {comment}")
            lines.append(f"$ {command}")
            if output:
                lines.append(str(output).rstrip())
        return "```terminal\n" + "\n".join(lines) + "\n```" if lines else ""
    if name == "AgentReplay":
        lines = ["*Agent session:*", ""]
        for event in _children(node):
            if event.name == "AgentPrompt":
                lines.append(f"- **Asked:** {_arg(event, 0)}")
            elif event.name == "AgentStep":
                lines.append(f"- {_arg(event, 1) or _arg(event, 0)}")
            elif event.name == "AgentAnswer":
                lines.append(f"- **Answered:** {_arg(event, 0)}")
                if _arg(event, 1):
                    lines.append(f"\n```\n{str(_arg(event, 1)).rstrip()}\n```")
        return "\n".join(lines)
    if name == "Chat":
        return "\n\n".join(
            f"**{'Q' if _arg(message, 0) == 'user' else 'A'}:** {str(_arg(message, 1)).strip()}"
            for message in _children(node)
        )
    if name in ("Figure", "Diagram"):
        caption = _arg(node, 2) if name == "Diagram" else _arg(node, 3)
        return f"*Figure: {_arg(node, 0)}*" + (f" {caption}" if caption else "")
    if name == "Artifact":
        return f"*Interactive: {_arg(node, 0)}*"
    return ""


def to_markdown(root: Node) -> str:
    """Flatten a page into Markdown: the text kept, drawings and widgets named."""
    blocks = _arg(root, 0, [])
    return "\n\n".join(part for part in (_block(b) for b in blocks) if part).strip()
