#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
from pathlib import Path
import sys
import time
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

DEFAULT_URL = "https://api.maxplus-ai.cc/v1/responses"
DEFAULT_MODEL = "gpt-5.5"
DEFAULT_OUT = "output/imagegen/output.png"


def die(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_api_key() -> Optional[str]:
    for name in ("MAXPLUS_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(name)
        if value:
            return value.strip()
    for raw in ("/tmp/maxplus_api_key", "/tmp/openai_api_key"):
        path = Path(raw)
        if path.exists():
            value = path.read_text(encoding="utf-8").strip()
            if value:
                return value
    return None


def build_payload(model: str, prompt: str) -> Dict[str, Any]:
    return {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [{"type": "input_text", "text": prompt}],
            }
        ],
        "tools": [{"type": "image_generation"}],
    }


def call_responses(payload: Dict[str, Any], url: str, timeout: int) -> Dict[str, Any]:
    key = read_api_key()
    if not key:
        die("API key missing. Set MAXPLUS_API_KEY/OPENAI_API_KEY or write /tmp/maxplus_api_key.")
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        die(f"HTTP {exc.code}: {body[:2000]}")
    except urllib.error.URLError as exc:
        die(str(exc))
    except json.JSONDecodeError as exc:
        die(f"invalid JSON response: {exc}")
    return {}


def extract_images(data: Dict[str, Any]) -> List[str]:
    images: List[str] = []
    for item in data.get("output", []):
        if isinstance(item, dict) and item.get("type") == "image_generation_call" and item.get("result"):
            images.append(str(item["result"]))
    return images


def write_image(image_b64: str, out: Path, force: bool) -> None:
    if out.exists() and not force:
        die(f"Output exists: {out} (use --force to overwrite)")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(base64.b64decode(image_b64))
    print(f"Wrote {out} ({out.stat().st_size} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate an image through Responses image_generation")
    parser.add_argument("prompt_arg", nargs="*", help="Prompt words; appended if --prompt is not used")
    parser.add_argument("--prompt", help="Image prompt")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output image path")
    parser.add_argument("--model", default=os.getenv("IMAGEGEN_MODEL", DEFAULT_MODEL))
    parser.add_argument("--url", default=os.getenv("IMAGEGEN_URL", DEFAULT_URL))
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    prompt = args.prompt or " ".join(args.prompt_arg).strip()
    if not prompt:
        die("Missing prompt. Use --prompt or pass prompt words.")

    payload = build_payload(args.model, prompt)
    if args.dry_run:
        print(json.dumps({"url": args.url, "out": args.out, **payload}, indent=2, ensure_ascii=False))
        return 0

    print("Calling Responses image_generation tool. This can take up to a couple of minutes.", file=sys.stderr)
    started = time.time()
    data = call_responses(payload, args.url, args.timeout)
    images = extract_images(data)
    if not images:
        types = [item.get("type") for item in data.get("output", []) if isinstance(item, dict)]
        die(f"No image_generation_call result. Output types: {types}")
    print(f"Generation completed in {time.time() - started:.1f}s.", file=sys.stderr)
    write_image(images[0], Path(args.out), args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
