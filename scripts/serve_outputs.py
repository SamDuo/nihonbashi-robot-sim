"""Serve the testbed outputs/ directory for the Streamlit dashboard.

The Streamlit dashboard at analysis/dashboard.py embeds an iframe pointing
at http://localhost:8889/cesium_view.html which in turn fetches:

  /geo/shelters_<scenario>.geojson      per-scenario shelter usage
  /timeseries/agents_<scenario>.czml    time-animated agent positions

This script runs a tiny CORS-enabled HTTP server on port 8889 that serves
the outputs/ directory so those fetches resolve. Stop with Ctrl C.

Run order:
    python scripts/run_testbed.py            # writes outputs/
    python scripts/serve_outputs.py          # this file, port 8889
    python -m streamlit run analysis/dashboard.py
"""
from __future__ import annotations

import http.server
import os
import socketserver
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUTS = ROOT / "outputs"

PORT = 8889


class CORSRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        super().end_headers()

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.end_headers()

    def log_message(self, format: str, *args) -> None:
        sys.stderr.write("  HTTP " + (format % args) + "\n")


def main() -> int:
    if not OUTPUTS.exists():
        print(f"outputs/ not found at {OUTPUTS}; run scripts/run_testbed.py first")
        return 1

    base_url = f"http://localhost:{PORT}"
    print()
    print("=" * 64)
    print("  Outputs server ready")
    print("=" * 64)
    print(f"  Serving:    {OUTPUTS}")
    print(f"  Base URL:   {base_url}")
    print(f"  Twin view:  {base_url}/cesium_view.html?scenario=proactive&hour=14")
    print()
    print("  Stop the server with Ctrl C.")
    print("=" * 64)
    print()

    os.chdir(OUTPUTS)
    with socketserver.TCPServer(("127.0.0.1", PORT), CORSRequestHandler) as srv:
        try:
            srv.serve_forever()
        except KeyboardInterrupt:
            print("\n  stopping server")
            srv.shutdown()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
