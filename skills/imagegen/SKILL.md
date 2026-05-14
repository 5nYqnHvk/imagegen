---
name: imagegen
description: >
  Generate raster images through a local MaxPlus/OpenAI-compatible Responses image_generation tool.
  Use when user asks to create an image, generate picture/art/photo/illustration, or invokes /imagegen.
argument-hint: "<prompt> [--out path]"
allowed-tools: Bash
---

Generate images using the bundled local CLI:

```bash
python "$HOME/.claude/plugins/marketplaces/imagegen/skills/imagegen/scripts/image_gen.py" \
  --prompt "<prompt>" \
  --out "<output.png>"
```

## Defaults

- Output path: `output/imagegen/output.png` unless user specifies one.
- Backend URL: `https://api.maxplus-ai.cc/v1/responses`
- Model: `gpt-5.5`
- Tool: `[{"type":"image_generation"}]`

## API key

Script reads key from first available source:

1. `MAXPLUS_API_KEY`
2. `OPENAI_API_KEY`
3. `/tmp/maxplus_api_key`
4. `/tmp/openai_api_key`

Never print keys.

## Workflow

1. Use the user-provided arguments as the prompt.
2. If no output path is specified, save to `output/imagegen/output.png`.
3. Run the bundled script.
4. Report saved path and file size.

Use `--force` only when overwriting is intended or output is a temp/new path.
