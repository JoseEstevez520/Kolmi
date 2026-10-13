// Trimming a list of siblings down to the context around one of them, for the previews that
// draw a piece of the tree (move, create) and for anything else that wants "this item and a
// little around it". Pure: no tree, no API.

// `focus` is the index of the item to keep (or where a new one would go: it may equal
// list.length, or be -1 for "none", which keeps the first `max`). Keeps at most `max` other
// items, taking the nearest ones on both sides, in their order. `hidden` counts what is left out.
export function trimAround(list, focus = -1, max = 2) {
  const keep = new Set()
  if (focus < 0) {
    for (let i = 0; i < Math.min(max, list.length); i++) keep.add(i)
  } else {
    if (focus < list.length) keep.add(focus)
    let before = focus - 1
    let after = focus < list.length ? focus + 1 : focus
    let room = max
    while (room > 0 && (before >= 0 || after < list.length)) {
      if (before >= 0) {
        keep.add(before--)
        room--
      }
      if (room > 0 && after < list.length) {
        keep.add(after++)
        room--
      }
    }
  }
  return {
    items: list.filter((_, i) => keep.has(i)),
    hidden: list.length - keep.size,
  }
}
