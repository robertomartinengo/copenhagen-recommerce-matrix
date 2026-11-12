"""Keep Render free-tier service awake by polling /zones periodically.

Reads API_URL from the environment. Uses only the Python standard library
so no new dependencies are required. Run as a cron job or background task;
do not commit secrets — API_URL must come from the environment.
"""

import os
import time
import urllib.request
import urllib.error

POLL_INTERVAL_SECONDS = 600  # 10 minutes


def poll_once() -> None:
    api_url = os.getenv("API_URL", "").strip()
    if not api_url:
        print("[keep_alive] API_URL not set; skipping poll.", flush=True)
        return

    target = api_url.rstrip("/") + "/zones"
    try:
        req = urllib.request.Request(target, method="GET")
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = resp.read(200)  # read only a small prefix
            print(
                f"[keep_alive] GET {target} -> HTTP {resp.status} "
                f"(body starts with {body[:80]!r})",
                flush=True,
            )
    except urllib.error.URLError as exc:
        print(f"[keep_alive] GET {target} failed: {exc}", flush=True)
    except Exception as exc:  # noqa: BLE001 - keep the loop alive
        print(f"[keep_alive] unexpected error: {exc}", flush=True)


def main() -> None:
    while True:
        poll_once()
        time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
