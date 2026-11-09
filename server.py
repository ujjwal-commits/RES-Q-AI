"""RESQ-AI server.  Run:  python server.py

Uses only Python's built-in web server, so the only things to install are
pandas and scikit-learn. Opens the dashboard in your browser automatically.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from resq.envfile import load_local_env              # noqa: E402
load_local_env(BASE / ".env")
from resq import auth                                 # noqa: E402
from resq.dataset import CSV_PATH, write_csv          # noqa: E402
from resq.demo import DEMO_REPORTS                    # noqa: E402
from resq.engine import TIERS                         # noqa: E402
from resq.evaluation import run_checks                # noqa: E402
from resq.locations import public_view, resource_points_view                # noqa: E402
from resq.model import Brain                          # noqa: E402
from resq.pipeline import Analyzer                    # noqa: E402
from resq.store import Store                          # noqa: E402

INDEX_HTML = BASE / "static" / "index.html"
MAX_REPORT_CHARS = 600

STATE = {"brain": None, "analyzer": None, "store": None, "metrics": None}


def load_everything(keep: bool):
    if not Path(CSV_PATH).exists():
        print("Dataset not found, generating the synthetic demo dataset ...")
        write_csv()
    print("Training the AI models ...", end=" ", flush=True)
    t = time.time()
    STATE["brain"] = Brain(CSV_PATH)
    STATE["analyzer"] = Analyzer(STATE["brain"])
    print("done in %.1fs (%d training reports)" % (time.time() - t, len(STATE["brain"].df)))
    STATE["store"] = Store(BASE / "data" / "resq.db", fresh=not keep)

    def _metrics():
        try:
            STATE["metrics"] = run_checks(STATE["brain"], STATE["analyzer"])
        except Exception as exc:  # metrics are a bonus, never crash the app for them
            STATE["metrics"] = {"error": str(exc)}

    threading.Thread(target=_metrics, daemon=True).start()


def incidents_payload():
    store = STATE["store"]
    items = store.active()
    counts = {t: 0 for t in TIERS}
    for i in items:
        counts[i["priority"]] += 1
    return {
        "now": time.time(), "incidents": items, "counts": counts,
        "handled": store.handled_count(), "recent_handled": store.recent_handled(),
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "RESQ-AI"

    def log_message(self, fmt, *args):     # keep the terminal quiet
        pass

    # ---- helpers
    def _send(self, code, body: bytes, ctype="application/json; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode("utf-8"))

    def _body(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
            return json.loads(self.rfile.read(n) or b"{}")
        except (ValueError, json.JSONDecodeError):
            return None

    def _session(self):
        """The logged-in user for this request, or None. Reads 'Authorization: Bearer <token>'."""
        header = self.headers.get("Authorization") or ""
        token = header[7:] if header.startswith("Bearer ") else ""
        return auth.session_for(token) if token else None

    # ---- routes
    def do_GET(self):
        path = self.path.split("?")[0]
        if path in ("/", "/index.html"):
            return self._send(200, INDEX_HTML.read_bytes(), "text/html; charset=utf-8")
        if path == "/favicon.ico":
            return self._send(204, b"")
        if path == "/api/incidents":
            return self._json(incidents_payload())
        if path == "/api/meta":
            brain = STATE["brain"]
            return self._json({
                "locations": public_view(),
                "resource_points": resource_points_view(),
                "tiers": TIERS,
                "training_rows": int(len(brain.df)),
                "metrics": STATE["metrics"],
                "roster": auth.roster(),
            })
        if path == "/api/export.csv":
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow(["id", "reported_at", "status", "report", "type", "priority", "score",
                        "confidence", "location", "people", "resources", "reported_by", "handled_by", "handled_at"])
            for i in STATE["store"].everything():
                w.writerow([i["id"], time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i["created_at"])),
                            i["status"], i["text"], i["type"], i["priority"], i["score"], i["confidence"],
                            i["location"] or "", i["people"] or "", "; ".join(r["name"] for r in i["resources"]),
                            i["reported_by"] or "", i["handled_by"] or "",
                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(i["handled_at"])) if i["handled_at"] else ""])
            return self._send(200, buf.getvalue().encode("utf-8-sig"), "text/csv; charset=utf-8",
                              {"Content-Disposition": 'attachment; filename="resq-ai-incident-log.csv"'})
        self._json({"error": "Not found"}, 404)

    def do_POST(self):
        path = self.path.split("?")[0]
        store, analyzer = STATE["store"], STATE["analyzer"]

        if path == "/api/report":
            data = self._body()
            text = (data or {}).get("text", "") if isinstance(data, dict) else ""
            text = " ".join(str(text).split())
            if not text:
                return self._json({"error": "Type or paste a report first."}, 400)
            if len(text) > MAX_REPORT_CHARS:
                return self._json({"error": "Report is too long. Keep it under %d characters." % MAX_REPORT_CHARS}, 400)
            return self._json(store.add(text, analyzer.analyze(text), reported_by="Public Demo"))

        if path == "/api/preview":
            # Analyses text WITHOUT saving it, used by the "compare wording" tool.
            data = self._body()
            text = (data or {}).get("text", "") if isinstance(data, dict) else ""
            text = " ".join(str(text).split())
            if not text:
                return self._json({"error": "Nothing to analyse."}, 400)
            if len(text) > MAX_REPORT_CHARS:
                return self._json({"error": "Too long. Keep it under %d characters." % MAX_REPORT_CHARS}, 400)
            return self._json(analyzer.analyze(text, night=False))

        if path == "/api/demo":
            store.clear()
            now = time.time()
            for text, minutes in DEMO_REPORTS:
                store.add(text, analyzer.analyze(text), created_at=now - minutes * 60, reported_by="Demo scenario")
            return self._json(incidents_payload())

        if path == "/api/clear":
            store.clear()
            return self._json(incidents_payload())

        if path == "/api/login":
            data = self._body() or {}
            username = str(data.get("username", ""))
            password = str(data.get("password", ""))
            result = auth.login(username, password)
            if not result:
                return self._json({"error": "Incorrect username or password."}, 401)
            return self._json(result)

        if path == "/api/logout":
            header = self.headers.get("Authorization") or ""
            token = header[7:] if header.startswith("Bearer ") else ""
            if token:
                auth.logout(token)
            return self._json({"ok": True})

        m = re.fullmatch(r"/api/incidents/(\d+)/resolve", path)
        if m:
            ok = store.resolve(int(m.group(1)), handled_by="Public Demo")
            return self._json(incidents_payload() if ok else {"error": "Incident not found"}, 200 if ok else 404)

        self._json({"error": "Not found"}, 404)


def main():
    ap = argparse.ArgumentParser(description="RESQ-AI dashboard server")
    ap.add_argument("--host", default=os.environ.get("HOST", "127.0.0.1"))
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT", "8000")))
    ap.add_argument("--keep", action="store_true", help="keep reports from the previous run")
    ap.add_argument("--no-browser", action="store_true", help="do not open the browser automatically")
    args = ap.parse_args()

    load_everything(args.keep)

    server = None
    for port in range(args.port, args.port + 10):
        try:
            server = ThreadingHTTPServer((args.host, port), Handler)
            break
        except OSError:
            continue
    if server is None:
        sys.exit("Could not find a free port. Close other programs and try again.")

    display_host = "127.0.0.1" if args.host in ("0.0.0.0", "::") else args.host
    url = "http://%s:%d" % (display_host, server.server_address[1])
    print("\nRESQ-AI is running at %s" % url)
    print("Keep this window open during the demo. Press Ctrl+C to stop.\n")
    if not args.no_browser:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
