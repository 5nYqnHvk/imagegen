---
name: imagegen
description: >
  Generate or edit raster images through the MaxPlus/OpenAI-compatible Images API
  (POST /v1/images/generations, model gpt-image-2). Use when user asks to create or
  edit an image, generate picture/art/photo/illustration, or invokes /imagegen.
argument-hint: "<prompt> [--out path] [--size 1024x1024] [--ref image.png]"
allowed-tools: Bash
---

Generate images using the bundled local CLI:

```bash
python "$HOME/.claude/plugins/marketplaces/imagegen/skills/imagegen/scripts/image_gen.py" \
  --prompt "<prompt>" \
  --out "<output.png>"
```

Edit / use reference images (proxy forwards to upstream `/v1/images/edits`, max 5 refs):

```bash
python "$HOME/.claude/plugins/marketplaces/imagegen/skills/imagegen/scripts/image_gen.py" \
  --prompt "Keep the product shape, place it on a beige studio surface" \
  --ref product.png \
  --out "<edited.png>"
```

## Defaults

- Output path: `output/imagegen/output.png` unless user specifies one.
- Backend URL: `https://api.maxplus-ai.cc/v1/images/generations`
- Model: `gpt-image-2`
- `--response-format`: `b64_json` (saved to file). Use `url` for a quick link.

## Options

- `--n` number of images (default 1; upstream caps via `GPT_IMAGE_MAX_IMAGES`, default 4). Extra images save as `name_2.png`, `name_3.png`, ...
- `--size` only `1024x1024` or `2048x2048`. Omit to use upstream default.
- `--quality`, `--output-format` (png/jpeg/webp), `--output-compression` (jpeg/webp only).
- `--ref PATH` reference image (repeatable, up to 5). png/jpeg/webp, ≤10MB each, ≤25MB total.
- `--user` optional end-user id for tracing.

## API key

Requires a key bound to the **Gen Image** pool. Script reads key from first available source:

1. `MAXPLUS_API_KEY`
2. `OPENAI_API_KEY`
3. `/tmp/maxplus_api_key`
4. `/tmp/openai_api_key`

Never print keys.

## Workflow

1. Use the user-provided arguments as the prompt.
2. If no output path is specified, save to `output/imagegen/output.png`.
3. For edits, pass each source image with `--ref` and describe what to keep vs change.
4. Run the bundled script.
5. Report saved path(s) and file size.

Use `--force` only when overwriting is intended or output is a temp/new path.
