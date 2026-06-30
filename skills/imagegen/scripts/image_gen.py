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

DEFAULT_URL = "https://api.maxplus-ai.cc/v1/images/generations"
DEFAULT_MODEL = "gpt-image-2"
DEFAULT_OUT = "output/imagegen/output.png"
SUPPORTED_SIZES = ("1024x1024", "2048x2048")
MAX_REFERENCE_IMAGES = 5
MAX_REFERENCE_BYTES = 10 * 1024 * 1024
MAX_REFERENCE_TOTAL = 25 * 1024 * 1024

# magic-byte signature -> upstream media_type
MEDIA_SIGNATURES = (
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
)


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


def detect_media_type(data: bytes) -> Optional[str]:
    for signature, media_type in MEDIA_SIGNATURES:
        if data.startswith(signature):
            return media_type
    # WEBP: "RIFF"...."WEBP"
    if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "image/webp"
    return None


def load_reference_images(paths: List[str]) -> List[Dict[str, str]]:
    if len(paths) > MAX_REFERENCE_IMAGES:
        die(f"Too many reference images: {len(paths)} (max {MAX_REFERENCE_IMAGES})")
    refs: List[Dict[str, str]] = []
    total = 0
    for raw in paths:
        path = Path(raw)
        if not path.exists():
            die(f"Reference image not found: {path}")
        blob = path.read_bytes()
        if len(blob) > MAX_REFERENCE_BYTES:
            die(f"Reference image too large: {path} ({len(blob)} bytes, max {MAX_REFERENCE_BYTES})")
        total += len(blob)
        if total > MAX_REFERENCE_TOTAL:
            die(f"Reference images exceed total size limit ({MAX_REFERENCE_TOTAL} bytes)")
        media_type = detect_media_type(blob)
        if not media_type:
            die(f"Unsupported reference image type: {path} (need png/jpeg/webp)")
        refs.append(
            {
                "media_type": media_type,
                "data": base64.b64encode(blob).decode("ascii"),
                "name": path.name,
            }
        )
    return refs


def build_payload(args: argparse.Namespace, references: List[Dict[str, str]]) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "model": args.model,
        "prompt": args.prompt,
        "n": args.n,
        "response_format": args.response_format,
    }
    if args.size:
        payload["size"] = args.size
    if args.quality:
        payload["quality"] = args.quality
    if args.output_format:
        payload["output_format"] = args.output_format
    if args.output_compression is not None:
        payload["output_compression"] = args.output_compression
    if args.user:
        payload["user"] = args.user
    if references:
        payload["reference_images"] = references
    return payload


def call_images(payload: Dict[str, Any], url: str, timeout: int) -> Dict[str, Any]:
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


def fetch_url_bytes(image_url: str, timeout: int) -> bytes:
    try:
        with urllib.request.urlopen(image_url, timeout=timeout) as resp:
            return resp.read()
    except urllib.error.URLError as exc:
        die(f"failed to download image url: {exc}")
    return b""


def extract_image_bytes(data: Dict[str, Any], timeout: int) -> List[bytes]:
    items = data.get("data")
    if not isinstance(items, list) or not items:
        die(f"No image data in response. Keys: {list(data.keys())}")
    images: List[bytes] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if item.get("b64_json"):
            images.append(base64.b64decode(item["b64_json"]))
        elif item.get("url"):
            images.append(fetch_url_bytes(str(item["url"]), timeout))
    if not images:
        die("Response contained no b64_json or url fields.")
    return images


def output_paths(base: Path, count: int) -> List[Path]:
    if count <= 1:
        return [base]
    paths = [base]
    for index in range(2, count + 1):
        paths.append(base.with_name(f"{base.stem}_{index}{base.suffix}"))
    return paths


def write_images(images: List[bytes], out: Path, force: bool) -> None:
    targets = output_paths(out, len(images))
    out.parent.mkdir(parents=True, exist_ok=True)
    for blob, target in zip(images, targets):
        if target.exists() and not force:
            die(f"Output exists: {target} (use --force to overwrite)")
        target.write_bytes(blob)
        print(f"Wrote {target} ({target.stat().st_size} bytes)")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate or edit images through the /v1/images/generations endpoint"
    )
    parser.add_argument("prompt_arg", nargs="*", help="Prompt words; appended if --prompt is not used")
    parser.add_argument("--prompt", help="Image prompt")
    parser.add_argument("--out", default=DEFAULT_OUT, help="Output image path")
    parser.add_argument("--model", default=os.getenv("IMAGEGEN_MODEL", DEFAULT_MODEL))
    parser.add_argument("--url", default=os.getenv("IMAGEGEN_URL", DEFAULT_URL))
    parser.add_argument("--n", type=int, default=1, help="Number of images (default 1)")
    parser.add_argument("--size", choices=SUPPORTED_SIZES, help="1024x1024 or 2048x2048")
    parser.add_argument(
        "--response-format",
        default="b64_json",
        choices=("b64_json", "url"),
        help="b64_json (default, save to file) or url",
    )
    parser.add_argument("--quality", help="Optional upstream quality, e.g. high")
    parser.add_argument(
        "--output-format",
        choices=("png", "jpeg", "webp"),
        help="Optional upstream output format",
    )
    parser.add_argument(
        "--output-compression",
        type=int,
        help="Compression (jpeg/webp only)",
    )
    parser.add_argument("--user", help="Optional end-user id for tracing")
    parser.add_argument(
        "--ref",
        action="append",
        default=[],
        metavar="PATH",
        help="Reference image path (repeatable, up to 5) -> triggers image edit",
    )
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    args.prompt = args.prompt or " ".join(args.prompt_arg).strip()
    if not args.prompt:
        die("Missing prompt. Use --prompt or pass prompt words.")
    if args.n < 1:
        die("--n must be >= 1")
    if args.output_compression is not None and args.output_format not in ("jpeg", "webp"):
        die("--output-compression requires --output-format jpeg or webp")

    references = load_reference_images(args.ref)
    payload = build_payload(args, references)

    if args.dry_run:
        preview = json.loads(json.dumps(payload))
        for ref in preview.get("reference_images", []):
            ref["data"] = f"<base64 {len(ref['data'])} chars>"
        print(json.dumps({"url": args.url, "out": args.out, **preview}, indent=2, ensure_ascii=False))
        return 0

    mode = "image edit" if references else "image generation"
    print(f"Calling {args.url} ({mode}). This can take up to a couple of minutes.", file=sys.stderr)
    started = time.time()
    data = call_images(payload, args.url, args.timeout)
    images = extract_image_bytes(data, args.timeout)
    print(f"Generation completed in {time.time() - started:.1f}s.", file=sys.stderr)
    write_images(images, Path(args.out), args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
