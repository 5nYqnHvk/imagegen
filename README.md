# imagegen

Claude Code plugin for generating and editing raster images through the MaxPlus/OpenAI-compatible Images API (`POST /v1/images/generations`, model `gpt-image-2`).

## Structure

```text
imagegen/
├── .claude-plugin/plugin.json
└── skills/
    └── imagegen/
        ├── SKILL.md
        └── scripts/image_gen.py
```

## Install

Claude Code from GitHub after this repo is pushed:

```bash
claude plugin marketplace add 5nYqnHvk/imagegen && claude plugin install imagegen@imagegen
```

Claude Code local install:

```bash
claude plugin marketplace add ~/.claude/plugins/marketplaces/imagegen && claude plugin install imagegen@imagegen
```

Codex:

```text
Clone/open this repo in Codex, then use the plugin UI or load AGENTS.md.
AGENTS.md imports ./skills/imagegen/SKILL.md.
```

After install, restart Claude Code if `/imagegen` is not visible yet.

## Backend

Default backend:

- URL: `https://api.maxplus-ai.cc/v1/images/generations`
- model: `gpt-image-2`
- body: JSON with `prompt`, `n`, `size`, `response_format`, optional `reference_images`
- requires an API key bound to the **Gen Image** pool

## Auth

Script reads API key from first available source:

1. `MAXPLUS_API_KEY`
2. `OPENAI_API_KEY`
3. `/tmp/maxplus_api_key`
4. `/tmp/openai_api_key`

## Usage

Generate:

```bash
python ~/.claude/plugins/marketplaces/imagegen/skills/imagegen/scripts/image_gen.py \
  --prompt "white cat on blue screen background" \
  --size 1024x1024 \
  --out output/imagegen/cat.png \
  --force
```

Edit with reference image(s) (up to 5; proxy forwards to upstream `/v1/images/edits`):

```bash
python ~/.claude/plugins/marketplaces/imagegen/skills/imagegen/scripts/image_gen.py \
  --prompt "Keep the product shape, place it on a beige studio surface" \
  --ref product.png \
  --output-format jpeg --output-compression 85 \
  --out output/imagegen/edited.jpg --force
```

Key options: `--n`, `--size` (`1024x1024` | `2048x2048`), `--response-format` (`b64_json` | `url`),
`--quality`, `--output-format` (`png`|`jpeg`|`webp`), `--output-compression`, `--ref` (repeatable), `--user`.

From Claude Code after plugin load:

```text
/imagegen white cat on blue screen background
```
