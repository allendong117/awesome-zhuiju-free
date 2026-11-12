#!/usr/bin/env python3
"""Read-only, dependency-free resource directory API. Python 3.10+."""
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlsplit
from urllib.request import Request, urlopen

OWNER = os.getenv("SOURCE_REPO", "allendong117/awesome-zhuiju-free")
BRANCH = os.getenv("SOURCE_BRANCH", "main")
PORT = int(os.getenv("PORT", "8787"))
PUBLIC_BASE_URL = os.getenv("PUBLIC_BASE_URL", "").rstrip("/")
TTL = max(60, int(os.getenv("CACHE_SECONDS", "900")))
ROOT = f"https://raw.githubusercontent.com/{OWNER}/{BRANCH}"
_cache = {}
_lock = threading.Lock()


def source_json(path):
    now = time.monotonic()
    with _lock:
        found = _cache.get(path)
        if found and now - found[0] < TTL:
            return found[1]
    request = Request(f"{ROOT}/{path}", headers={"User-Agent": "zhuiju-directory-api/1.0"})
    with urlopen(request, timeout=12) as response:
        result = json.load(response)
    with _lock:
        _cache[path] = (time.monotonic(), result)
    return result


def search(q="", category="", status="", limit=30, copyright_risk=""):
    resources = source_json("resources/resources.json").get("resources", [])
    report = source_json("reports/availability.json")
    states = {x["resource_id"]: x for x in report.get("results", [])}
    term = q.casefold().strip()
    items = []
    for item in resources:
        state = states.get(item.get("id"), {})
        if category and item.get("category") != category:
            continue
        if status and state.get("status", "unknown") != status:
            continue
        if copyright_risk and item.get("risks", {}).get("copyright", "unknown") != copyright_risk:
            continue
        haystack = " ".join(str(x) for x in (
            item.get("name", ""), item.get("summary", ""), " ".join(item.get("tags", []))
        )).casefold()
        if term and term not in haystack:
            continue
        items.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "url": item.get("url"),
            "category": item.get("category"),
            "summary": item.get("summary_short") or item.get("summary"),
            "tags": item.get("tags", []),
            "copyright_risk": item.get("risks", {}).get("copyright", "unknown"),
            "verification": item.get("verification", {}).get("status", "unknown"),
            "status": state.get("status", "unknown"),
            "http_status": state.get("http_status"),
            "checked_at": state.get("checked_at"),
        })
        if len(items) >= limit:
            break
    return {"count": len(items), "results": items, "report_generated_at": report.get("generated_at")}


def openapi():
    # Set PUBLIC_BASE_URL to a publicly reachable HTTPS address before connecting a GPT Action.
    server = [{"url": PUBLIC_BASE_URL}] if PUBLIC_BASE_URL else []
    return {
        "openapi": "3.1.0",
        "info": {"title": "Zhuiju Resource Directory", "version": "1.0.0",
                 "description": "Read-only site directory; search results are not proof of copyright authorization."},
        "servers": server,
        "paths": {
            "/resources": {"get": {
                "operationId": "searchResources",
                "summary": "Search categorized site listings and access status",
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                    {"name": "category", "in": "query", "schema": {"type": "string", "enum": [
                        "online_video", "video_app", "subtitles", "player", "subscription",
                        "tvbox_config", "magnet_search", "cloud_search", "open_source"]}},
                    {"name": "status", "in": "query", "schema": {"type": "string",
                        "enum": ["reachable", "restricted", "unreachable", "unknown"]}},
                    {"name": "copyright_risk", "in": "query", "schema": {"type": "string",
                        "enum": ["low", "medium", "high", "unknown"]}},
                    {"name": "limit", "in": "query", "schema": {"type": "integer", "minimum": 1, "maximum": 100}}
                ],
                "responses": {"200": {"description": "Matching directory entries",
                    "content": {"application/json": {"schema": {"type": "object"}}}}}
            }},
            "/health": {"get": {"operationId": "healthCheck", "summary": "Check API health",
                "responses": {"200": {"description": "API running"}}}}
        }
    }


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body):
        payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "public, max-age=60")
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        parsed = urlsplit(self.path)
        params = parse_qs(parsed.query)
        def param(name, default=""):
            return params.get(name, [default])[0]
        if parsed.path == "/health":
            return self.reply(200, {"ok": True, "source_repo": OWNER})
        if parsed.path == "/openapi.json":
            return self.reply(200, openapi())
        if parsed.path != "/resources":
            return self.reply(404, {"error": "not_found"})
        try:
            limit = int(param("limit", "30"))
            if limit < 1 or limit > 100:
                return self.reply(400, {"error": "limit must be between 1 and 100"})
            return self.reply(200, search(param("q"), param("category"), param("status"),
                                          limit, param("copyright_risk")))
        except (ValueError, TypeError) as exc:
            return self.reply(400, {"error": str(exc)})
        except Exception:
            return self.reply(503, {"error": "source_data_unavailable"})

if __name__ == "__main__":
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
