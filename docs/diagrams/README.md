# Diagrams

Editable draw.io sources and exported SVGs used in the docs.

| Source | Export | Used in |
| --- | --- | --- |
| `pipeline.drawio` | `pipeline.svg` | `README.md`, `guide/architecture.md` |
| `epi-methodology.drawio` | `epi-methodology.svg` | `guide/methodology.md` |
| `data-model.drawio` | `data-model.svg` | `guide/architecture.md` |

The `.drawio` files are the source of truth. Do not hand-edit the SVGs.

## Edit and re-export

```sh
# edit visually:
drawio docs/diagrams/pipeline.drawio
# re-export (run from repo root):
drawio -x -f svg -o docs/diagrams/pipeline.svg docs/diagrams/pipeline.drawio
```

## Shared style

- Vertices: `rounded=1;fillColor=#ffffff;strokeColor=#2f6f72;fontColor=#1a1c1e` (process steps use the accent fill `#e6f0f0`).
- Edges: `edgeStyle=orthogonalEdgeStyle;rounded=1;strokeColor=#6b7177`.
- Each diagram sits inside a light panel container (`#fbfbfa`) so it stays legible on GitHub light and dark themes.

Lint before committing (catches overlaps / dangling edges):

```sh
python3 ~/.claude/skills/drawio-skill/scripts/validate.py docs/diagrams/<name>.drawio
```

PNG exports are only for visual review and are gitignored.
