"""Simple logger that prints timestamped messages (Unicode-safe for Windows)."""
import sys
import os
from datetime import datetime

# Force UTF-8 output on Windows to prevent emoji crashes
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

def log(message: str):
    ts = datetime.now().strftime("%H:%M:%S")
    try:
        print(f"[{ts}] {message}", flush=True)
    except UnicodeEncodeError:
        # Strip non-ASCII characters as last resort
        safe = message.encode("ascii", errors="replace").decode("ascii")
        print(f"[{ts}] {safe}", flush=True)
