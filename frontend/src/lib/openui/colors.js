// The figure palette: a few concept colours and the three outcomes, by name. Each is a
// `--diagram-color`, which elastic-ui mixes into a soft tint and a label that read on light and
// dark (tokens.css). Kept free of imports so the prompt generator can load it in Node.
export const COLOR_VALUES = {
  blue: '#2563eb',
  violet: '#7c3aed',
  cyan: '#0891b2',
  pink: '#db2777',
  yellow: '#ca8a04',
  grey: 'var(--color-fg-muted)',
  green: 'var(--color-success)',
  amber: 'var(--color-warning)',
  red: 'var(--color-danger)',
}

export const COLORS = Object.keys(COLOR_VALUES)
