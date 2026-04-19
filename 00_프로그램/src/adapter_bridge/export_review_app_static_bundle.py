from __future__ import annotations

import argparse
import copy
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any

import run_question_review_server as review_server


PATH_FIELD_NAMES = {
    "question_file",
    "review_image",
    "page_read_manifest_path",
    "manifest_path",
    "metadata_path",
    "source_pdf_path",
    "page_image_path",
    "image_path",
    "input_path",
    "output_path",
    "request_package_path",
}


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_local_path_string(value: str) -> bool:
    if re.match(r"^[A-Za-z]:[\\/]", value):
        return True
    normalized = value.replace("/", "\\")
    for root in (review_server.DATA_ROOT, review_server.PROGRAM_ROOT):
        root_text = str(root).replace("/", "\\")
        if normalized.startswith(root_text):
            return True
    return False


def sanitize_for_static(value: Any) -> Any:
    if isinstance(value, dict):
        output: dict[str, Any] = {}
        for key, item in value.items():
            if key in PATH_FIELD_NAMES:
                continue
            cleaned = sanitize_for_static(item)
            if cleaned is not None:
                output[key] = cleaned
        return output
    if isinstance(value, list):
        return [item for item in (sanitize_for_static(item) for item in value) if item is not None]
    if isinstance(value, str) and is_local_path_string(value):
        return None
    return value


def slug_fragment(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "_", value).strip("._-")
    return slug[:48] or "source"


def static_page_filename(unit: str, category: str, source_stem: str, page_number: int) -> str:
    digest = hashlib.sha1(f"{unit}\0{category}\0{source_stem}\0{page_number}".encode("utf-8")).hexdigest()[:12]
    return f"pages/{slug_fragment(source_stem)}__p{page_number:03d}__{digest}.json"


def static_image_filename(unit: str, category: str, source_stem: str, page_number: int, extension: str) -> str:
    digest = hashlib.sha1(f"{unit}\0{category}\0{source_stem}\0{page_number}".encode("utf-8")).hexdigest()[:12]
    return f"images/{slug_fragment(source_stem)}__p{page_number:03d}__{digest}{extension}"


def ensure_safe_output_dir(output_dir: Path) -> Path:
    resolved = output_dir.resolve()
    app_root = review_server.APP_ROOT.resolve()
    try:
        resolved.relative_to(app_root)
    except ValueError as exc:
        raise SystemExit(f"Refusing to write outside review_app: {resolved}") from exc
    return resolved


def export_review_image(source_path: Path | None, output_dir: Path, relative_without_extension: str, max_width: int, quality: int) -> str | None:
    if source_path is None or not source_path.exists():
        return None

    try:
        from PIL import Image, ImageOps
    except ImportError as exc:
        raise SystemExit("Pillow is required for image export. Install Pillow or run with --skip-images.") from exc

    webp_relative = f"{relative_without_extension}.webp"
    webp_path = output_dir / webp_relative
    webp_path.parent.mkdir(parents=True, exist_ok=True)

    with Image.open(source_path) as image:
        image = ImageOps.exif_transpose(image)
        if max_width > 0 and image.width > max_width:
            ratio = max_width / image.width
            image = image.resize((max_width, max(1, round(image.height * ratio))), Image.Resampling.LANCZOS)
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGB")
        image.save(webp_path, "WEBP", quality=quality, method=6)

    return f"./data/{webp_relative.replace('\\', '/')}"


def iter_pages(library: dict[str, Any]):
    for unit_entry in library.get("units", []):
        unit = unit_entry["unit"]
        for category_entry in unit_entry.get("categories", []):
            category = category_entry["category"]
            for source_entry in category_entry.get("sources", []):
                source_stem = source_entry["source_stem"]
                for page_entry in source_entry.get("pages", []):
                    yield unit, category, source_stem, page_entry


def export_static_bundle(args: argparse.Namespace) -> dict[str, Any]:
    output_dir = ensure_safe_output_dir(Path(args.output_dir))
    if output_dir.exists() and not args.keep_existing:
        shutil.rmtree(output_dir)
    (output_dir / "pages").mkdir(parents=True, exist_ok=True)
    (output_dir / "images").mkdir(parents=True, exist_ok=True)

    library, page_index, version = review_server.discover_question_library()
    static_library = copy.deepcopy(library)

    for _unit, _category, source_stem, page_entry in iter_pages(static_library):
        page_number = int(page_entry["page_number"])
        page_entry["static_page_file"] = static_page_filename(_unit, _category, source_stem, page_number)

    state = review_server.AppState(library=static_library, page_index=page_index, version=version)

    page_count = 0
    question_count = 0
    image_count = 0
    missing_image_count = 0

    for unit, category, source_stem, page_entry in iter_pages(static_library):
        if args.limit_pages is not None and page_count >= args.limit_pages:
            break

        page_number = int(page_entry["page_number"])
        payload = review_server.build_page_with_navigation(state, unit, category, source_stem, page_number)
        if payload is None:
            continue

        static_image_url = None
        index_entry = page_index.get((unit, category, source_stem, page_number), {})
        if not args.skip_images:
            image_relative = static_image_filename(unit, category, source_stem, page_number, "")
            static_image_url = export_review_image(
                index_entry.get("review_image"),
                output_dir,
                image_relative,
                args.image_max_width,
                args.image_quality,
            )
            if static_image_url:
                image_count += 1
            else:
                missing_image_count += 1

        payload["review_image_url"] = static_image_url
        page_entry["review_image_url"] = static_image_url

        page_file = output_dir / page_entry["static_page_file"]
        write_json(page_file, sanitize_for_static(payload))
        page_count += 1
        question_count += int((payload.get("summary") or {}).get("question_count") or 0)

    sanitized_library = sanitize_for_static(static_library)
    write_json(output_dir / "library.json", sanitized_library)

    image_bytes = sum(path.stat().st_size for path in (output_dir / "images").glob("*") if path.is_file())
    summary = {
        "status": "ok",
        "source": "review_app",
        "workspace": review_server.DATA_ROOT.name,
        "output_dir": str(output_dir.relative_to(review_server.APP_ROOT).as_posix()),
        "version": list(version),
        "unit_count": len(sanitized_library.get("units", [])),
        "page_count": page_count,
        "question_count": question_count,
        "image_count": image_count,
        "missing_image_count": missing_image_count,
        "image_bytes": image_bytes,
        "skip_images": bool(args.skip_images),
    }
    write_json(output_dir / "export_summary.json", summary)
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export the existing review_app API payloads as static files.")
    parser.add_argument("--output-dir", default=str(review_server.APP_ROOT / "data"))
    parser.add_argument("--keep-existing", action="store_true", help="Do not delete the existing data directory first.")
    parser.add_argument("--skip-images", action="store_true", help="Export JSON only and leave source images out.")
    parser.add_argument("--image-max-width", type=int, default=1200)
    parser.add_argument("--image-quality", type=int, default=68)
    parser.add_argument("--limit-pages", type=int, default=None, help="Debug option: export only the first N pages.")
    return parser.parse_args()


def main() -> None:
    summary = export_static_bundle(parse_args())
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
