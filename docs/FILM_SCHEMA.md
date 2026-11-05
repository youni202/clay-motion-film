# film.json

One file describes a whole film. See `films/_sample/film.json` for a complete example.

| Field | Type | What it does |
|---|---|---|
| `slug` | string | Folder name and URL path (`dist/<slug>/`). |
| `title` | string | Browser tab title. |
| `brand` | string | Shown in the top chip, on each scene card and as the finale logo (plain text, not a logo image). |
| `since`, `now` | number | The intro counts from `since` to `now`. |
| `palette` | object | `primary`, `deep`, `light`, `accent`, `stage` hex colors. |
| `art_direction` | string | Extra style words added to every image prompt. |
| `characters` | object | `key: "English description"` for each clay animal. The first one becomes the style reference for the rest. |
| `hero` | string | Object shown above the year in the intro (e.g. "an emerald umbrella"). |
| `intro.sub` | string | Line under the year. `**bold**` is highlighted. |
| `history` | object | `title`, `sub`, `character` (key), `items`: `[[year, label, 1?], ...]`. 1 highlights a milestone. Up to 8 items. |
| `scenes` | array | 4–5 entries: `img` (character key), `name` (short uppercase word), `cat`, `bg`, `blob`, `ac` (accent), `how` (headline), `tip` (typed sentence), `tags` (3 chips), optional `status`. |
| `products` | object | `tag`, `title`, `sub`, `characters` (keys), `groups`: `[{label, items: [[name, caption, color, badge?]]}]`. Up to about 12 boxes. |
| `finale` | object | `title`, `sub`, `logo`. |
| `music` | object | `prompt` (English mood), `bpm`. The length is set automatically from `timing`. |
| `timing` | object | Seconds per section: `intro`, `history`, `scene`, `products`, `finale`. |
| `sources` | array | `{title, url}` for every fact used. |

## Copy length limits (1920×1080)
- `scenes[].name`: 10 letters or fewer.
- `how`: 16 Korean characters or fewer.
- `tip`: 70 or fewer.
- `history` labels: 14 or fewer.
- Product name: 18 or fewer. Caption: 10 or fewer.
