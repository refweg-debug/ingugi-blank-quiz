from __future__ import annotations

import argparse
import json
import mimetypes
import socket
import sys
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse


def detect_program_root() -> Path:
    cwd = Path.cwd()
    if (cwd / "src").exists() and (cwd / "config").exists():
        return cwd
    return Path(__file__).resolve().parents[2]


PROGRAM_ROOT = detect_program_root()
DATA_ROOT = PROGRAM_ROOT.parent
APP_ROOT = PROGRAM_ROOT / "review_app"
PROPOSITION_STAGE = "05_" + "\uba85\uc81c"
QUESTION_STAGE = "08_" + "\ubb38\ud56d"
CURRENT_STAGE = "09_" + "\ud604\uc7ac\ud1b5\ud569"
CURRENT_QUESTION_STAGE = "current_questions"
EXHAUSTIVE_TEXT_STAGE = "12_" + "\uc644\uc804\ud14d\uc2a4\ud2b8\uae30\ub85d"
SKIP_UNITS = {"00_" + "\ud504\ub85c\uadf8\ub7a8", "\uacf5\ud1b5\uc790\ub8cc"}


@dataclass
class AppState:
    library: dict[str, Any]
    page_index: dict[tuple[str, str, str, int], dict[str, Any]]
    version: tuple[int, int, int]


def json_response(handler: BaseHTTPRequestHandler, payload: Any, status: int = 200) -> None:
    body = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def text_response(
    handler: BaseHTTPRequestHandler,
    text: str,
    content_type: str = "text/plain; charset=utf-8",
    status: int = 200,
) -> None:
    body = text.encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", content_type)
    handler.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def compute_question_library_version() -> tuple[int, int, int]:
    count = 0
    latest_mtime_ns = 0
    total_size = 0
    for unit_dir in DATA_ROOT.iterdir():
        if not unit_dir.is_dir() or unit_dir.name in SKIP_UNITS:
            continue
        question_root = unit_dir / QUESTION_STAGE
        if not question_root.exists():
            continue
        for category_dir in question_root.iterdir():
            if not category_dir.is_dir():
                continue
            for path in category_dir.glob("*_questions.json"):
                try:
                    stat = path.stat()
                except OSError:
                    continue
                count += 1
                total_size += stat.st_size
                latest_mtime_ns = max(latest_mtime_ns, stat.st_mtime_ns)
    return count, latest_mtime_ns, total_size


def discover_question_library() -> tuple[dict[str, Any], dict[tuple[str, str, str, int], dict[str, Any]], tuple[int, int, int]]:
    units_payload: list[dict[str, Any]] = []
    page_index: dict[tuple[str, str, str, int], dict[str, Any]] = {}

    for unit_dir in sorted(DATA_ROOT.iterdir()):
        if not unit_dir.is_dir() or unit_dir.name in SKIP_UNITS:
            continue
        question_root = unit_dir / QUESTION_STAGE
        if not question_root.exists() and not (unit_dir / CURRENT_STAGE / CURRENT_QUESTION_STAGE).exists():
            continue

        categories_payload: list[dict[str, Any]] = []
        category_dirs: list[tuple[str, Path]] = []
        if question_root.exists():
            for category_dir in sorted(question_root.iterdir()):
                if category_dir.is_dir():
                    category_dirs.append((category_dir.name, category_dir))
        current_question_dir = unit_dir / CURRENT_STAGE / CURRENT_QUESTION_STAGE
        if current_question_dir.exists():
            category_dirs.insert(0, ("\ud604\uc7ac\ud1b5\ud569", current_question_dir))

        for category_name, category_dir in category_dirs:

            source_map: dict[str, dict[str, Any]] = {}
            for question_path in sorted(category_dir.glob("*_questions.json")):
                data = safe_read_json(question_path)
                if not data:
                    continue

                page_ref = data.get("page_ref", {})
                source_stem = str(page_ref.get("source_stem") or question_path.stem)
                page_number = int(page_ref.get("page_number") or 0)
                if page_number <= 0:
                    continue

                source_entry = source_map.setdefault(
                    source_stem,
                    {
                        "source_stem": source_stem,
                        "page_count": 0,
                        "question_total": 0,
                        "pages": [],
                    },
                )

                question_count = int(data.get("summary", {}).get("question_count") or 0)
                source_page_number = page_ref.get("source_page_number")
                if source_page_number is None:
                    source_page_number = page_ref.get("original_page_number")
                page_entry = {
                    "page_number": page_number,
                    "source_page_number": int(source_page_number) if source_page_number else None,
                    "question_count": question_count,
                    "finalization_status": data.get("finalization_status"),
                    "page_read_status": data.get("page_read_status"),
                    "question_file": str(question_path),
                    "review_image": page_ref.get("review_image"),
                }
                source_entry["pages"].append(page_entry)
                source_entry["page_count"] += 1
                source_entry["question_total"] += question_count
                page_index[(unit_dir.name, category_name, source_stem, page_number)] = {
                    "question_path": question_path,
                    "review_image": Path(page_ref["review_image"]) if page_ref.get("review_image") else None,
                }

            if not source_map:
                continue

            sources_payload: list[dict[str, Any]] = []
            for source_stem in sorted(source_map):
                source_entry = source_map[source_stem]
                source_entry["pages"].sort(key=lambda item: item["page_number"])
                sources_payload.append(source_entry)

            categories_payload.append(
                {
                    "category": category_name,
                    "source_count": len(sources_payload),
                    "sources": sources_payload,
                }
            )

        if categories_payload:
            units_payload.append(
                {
                    "unit": unit_dir.name,
                    "category_count": len(categories_payload),
                    "categories": categories_payload,
                }
            )

    return {"units": units_payload}, page_index, compute_question_library_version()


def load_page_payload(state: AppState, unit: str, category: str, source_stem: str, page_number: int) -> dict[str, Any] | None:
    entry = state.page_index.get((unit, category, source_stem, page_number))
    if not entry:
        return None
    return safe_read_json(entry["question_path"])


def stage_page_json_path(unit: str, stage: str, category: str, source_stem: str, page_number: int) -> Path:
    return DATA_ROOT / unit / stage / category / f"{source_stem}__p{page_number:03d}.json"


def resolve_note_analysis_ref(
    unit: str,
    category: str,
    source_stem: str,
    page_number: int,
    payload: dict[str, Any],
) -> tuple[str, str, int]:
    page_ref = payload.get("page_ref", {})
    if category == "\ud604\uc7ac\ud1b5\ud569" and page_ref.get("note_source_stem") and page_ref.get("note_page_number"):
        return "\ud544\uae30\ubcf8", str(page_ref["note_source_stem"]), int(page_ref["note_page_number"])
    return category, source_stem, page_number


def summarize_exhaustive_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None
    return {
        "extraction_status": payload.get("extraction_status"),
        "corrected_blocks": list(payload.get("corrected_blocks", [])),
        "supplemental_ocr_blocks": list(payload.get("supplemental_ocr_blocks", [])),
        "corrected_page_text": payload.get("corrected_page_text", ""),
        "quality_audit": payload.get("quality_audit", {}),
        "page_read_manifest_path": payload.get("page_read_manifest_path"),
    }


def summarize_proposition_payload(payload: dict[str, Any] | None) -> dict[str, Any] | None:
    if not payload:
        return None

    def statements(items: list[dict[str, Any]] | None, field_name: str = "learning_statement") -> list[str]:
        return [str(item.get(field_name, "")).strip() for item in items or [] if str(item.get(field_name, "")).strip()]

    return {
        "finalization_status": payload.get("finalization_status"),
        "page_block_source": (payload.get("source_snapshot") or {}).get("page_block_source"),
        "textual_record_status": ((payload.get("page_read_contract") or {}).get("textual_record_status")),
        "course_propositions": statements(payload.get("course_propositions")),
        "note_concept_inference_propositions": statements(payload.get("note_concept_inference_propositions")),
        "canonical_propositions": statements(payload.get("canonical_propositions")),
        "textbook_context_propositions": statements(payload.get("textbook_context_propositions")),
        "supportive_synthesized_propositions": statements(payload.get("supportive_synthesized_propositions")),
        "unresolved_notes": [
            {
                "block_index": item.get("block_index"),
                "text": item.get("text"),
                "reason": item.get("reason"),
            }
            for item in payload.get("unresolved_notes", [])
        ],
        "coverage_audit": payload.get("coverage_audit", {}),
    }


def attach_analysis_payload(unit: str, category: str, source_stem: str, page_number: int, payload: dict[str, Any]) -> dict[str, Any]:
    analysis_category, analysis_source_stem, analysis_page_number = resolve_note_analysis_ref(
        unit,
        category,
        source_stem,
        page_number,
        payload,
    )
    proposition_payload = safe_read_json(
        stage_page_json_path(unit, PROPOSITION_STAGE, analysis_category, analysis_source_stem, analysis_page_number)
    )
    note_exhaustive_payload = safe_read_json(
        stage_page_json_path(unit, EXHAUSTIVE_TEXT_STAGE, analysis_category, analysis_source_stem, analysis_page_number)
    )

    lecture_exhaustive_payload = None
    page_ref = payload.get("page_ref", {})
    lecture_source_stem = page_ref.get("original_source_stem")
    lecture_page_number = page_ref.get("original_page_number") or page_ref.get("source_page_number")
    if lecture_source_stem and lecture_page_number:
        lecture_exhaustive_payload = safe_read_json(
            stage_page_json_path(unit, EXHAUSTIVE_TEXT_STAGE, "\uac15\uc758\uc6d0\ubcf8", str(lecture_source_stem), int(lecture_page_number))
        )

    payload["analysis"] = {
        "analysis_ref": {
            "category": analysis_category,
            "source_stem": analysis_source_stem,
            "page_number": analysis_page_number,
        },
        "propositions": summarize_proposition_payload(proposition_payload),
        "note_exhaustive_text": summarize_exhaustive_payload(note_exhaustive_payload),
        "lecture_exhaustive_text": summarize_exhaustive_payload(lecture_exhaustive_payload),
    }
    return payload


def build_page_with_navigation(
    state: AppState,
    unit: str,
    category: str,
    source_stem: str,
    page_number: int,
) -> dict[str, Any] | None:
    payload = load_page_payload(state, unit, category, source_stem, page_number)
    if not payload:
        return None

    pages: list[dict[str, Any]] = []
    for unit_entry in state.library["units"]:
        if unit_entry["unit"] != unit:
            continue
        for category_entry in unit_entry["categories"]:
            if category_entry["category"] != category:
                continue
            for source_entry in category_entry["sources"]:
                if source_entry["source_stem"] == source_stem:
                    pages = source_entry["pages"]
                    break

    page_numbers = [item["page_number"] for item in pages]
    try:
        idx = page_numbers.index(page_number)
    except ValueError:
        idx = -1

    payload["navigation"] = {
        "pages": pages,
        "current_index": idx,
        "previous_page": page_numbers[idx - 1] if idx > 0 else None,
        "next_page": page_numbers[idx + 1] if idx >= 0 and idx + 1 < len(page_numbers) else None,
    }
    payload["review_image_url"] = (
        f"/api/review-image?unit={unit}&category={category}&source_stem={source_stem}&page={page_number}"
    )
    return attach_analysis_payload(unit, category, source_stem, page_number, payload)


def get_lan_addresses() -> list[str]:
    addresses: set[str] = set()
    try:
        hostname = socket.gethostname()
        for address in socket.gethostbyname_ex(hostname)[2]:
            if "." in address and not address.startswith("127."):
                addresses.add(address)
    except OSError:
        pass

    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.connect(("8.8.8.8", 80))
        ip = sock.getsockname()[0]
        if "." in ip and not ip.startswith("127."):
            addresses.add(ip)
    except OSError:
        pass
    finally:
        try:
            sock.close()
        except Exception:
            pass

    return sorted(addresses)


class ReviewRequestHandler(BaseHTTPRequestHandler):
    server_version = "IngugiReviewServer/1.0"

    @property
    def app_state(self) -> AppState:
        return self.server.app_state  # type: ignore[attr-defined]

    def ensure_library_current(self) -> None:
        current_version = compute_question_library_version()
        if current_version == self.app_state.version:
            return
        library, page_index, version = discover_question_library()
        self.server.app_state = AppState(library=library, page_index=page_index, version=version)  # type: ignore[attr-defined]

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        self.ensure_library_current()
        if parsed.path in {"/", "/index.html"}:
            return self.serve_static("index.html", "text/html; charset=utf-8")
        if parsed.path == "/app.js":
            return self.serve_static("app.js", "application/javascript; charset=utf-8")
        if parsed.path == "/app.css":
            return self.serve_static("app.css", "text/css; charset=utf-8")
        if parsed.path == "/api/library":
            return json_response(self, self.app_state.library)
        if parsed.path == "/api/refresh":
            library, page_index, version = discover_question_library()
            self.server.app_state = AppState(library=library, page_index=page_index, version=version)  # type: ignore[attr-defined]
            return json_response(self, {"status": "ok", "unit_count": len(library["units"])})
        if parsed.path == "/api/page":
            return self.serve_page(parsed.query)
        if parsed.path == "/api/review-image":
            return self.serve_review_image(parsed.query)

        return text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

    def log_message(self, format: str, *args: Any) -> None:
        sys.stdout.write("%s - - [%s] %s\n" % (self.address_string(), self.log_date_time_string(), format % args))

    def serve_static(self, filename: str, content_type: str) -> None:
        path = APP_ROOT / filename
        if not path.exists():
            return text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)
        text_response(self, path.read_text(encoding="utf-8"), content_type=content_type)

    def serve_page(self, query_string: str) -> None:
        query = parse_qs(query_string)
        try:
            unit = query["unit"][0]
            category = query["category"][0]
            source_stem = query["source_stem"][0]
            page_number = int(query["page"][0])
        except (KeyError, IndexError, ValueError):
            return json_response(self, {"error": "invalid_query"}, status=HTTPStatus.BAD_REQUEST)

        payload = build_page_with_navigation(self.app_state, unit, category, source_stem, page_number)
        if payload is None:
            return json_response(self, {"error": "page_not_found"}, status=HTTPStatus.NOT_FOUND)
        return json_response(self, payload)

    def serve_review_image(self, query_string: str) -> None:
        query = parse_qs(query_string)
        try:
            unit = query["unit"][0]
            category = query["category"][0]
            source_stem = query["source_stem"][0]
            page_number = int(query["page"][0])
        except (KeyError, IndexError, ValueError):
            return text_response(self, "invalid_query", status=HTTPStatus.BAD_REQUEST)

        entry = self.app_state.page_index.get((unit, category, source_stem, page_number))
        if not entry or not entry.get("review_image"):
            return text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        image_path: Path = entry["review_image"]
        if not image_path.exists():
            return text_response(self, "Not found", status=HTTPStatus.NOT_FOUND)

        mime_type = mimetypes.guess_type(image_path.name)[0] or "application/octet-stream"
        body = image_path.read_bytes()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", mime_type)
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="LAN browser UI for reviewing generated fill-blank questions.")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host. Use 0.0.0.0 for same-WiFi devices.")
    parser.add_argument("--port", type=int, default=8765, help="Bind port.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    library, page_index, version = discover_question_library()
    state = AppState(library=library, page_index=page_index, version=version)

    server = ThreadingHTTPServer((args.host, args.port), ReviewRequestHandler)
    server.app_state = state  # type: ignore[attr-defined]

    print("Question review server started.", flush=True)
    print(f"- program_root: {PROGRAM_ROOT}", flush=True)
    print(f"- data_root: {DATA_ROOT}", flush=True)
    print(f"- question_files: {len(page_index)}", flush=True)
    print(f"- local: http://127.0.0.1:{args.port}", flush=True)
    for ip in get_lan_addresses():
        print(f"- LAN:   http://{ip}:{args.port}", flush=True)
    print(f"- units: {len(library['units'])}", flush=True)
    print("Press Ctrl+C to stop.", flush=True)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
