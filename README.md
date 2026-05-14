# imagegen

Claude Code plugin for generating raster images through a local Responses `image_generation` tool wrapper.

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

- URL: `https://api.maxplus-ai.cc/v1/responses`
- model: `gpt-5.5`
- tool: `[{"type":"image_generation"}]`
- input: Responses array format

## Auth

Script reads API key from first available source:

1. `MAXPLUS_API_KEY`
2. `OPENAI_API_KEY`
3. `/tmp/maxplus_api_key`
4. `/tmp/openai_api_key`

## Usage

```bash
python ~/.claude/plugins/marketplaces/imagegen/skills/imagegen/scripts/image_gen.py \
  --prompt "white cat on blue screen background" \
  --out output/imagegen/cat.png \
  --force
```

From Claude Code after plugin load:

```text
/imagegen white cat on blue screen background
```
