import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = Path(__file__).resolve().parent  # zoo-code
PORT = 8000


def find_gateway_pids():
    """Trouve les PIDs des processus api_gateway via wmic."""
    pids = []
    try:
        r = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'", "get", "ProcessId,CommandLine"],
            capture_output=True, text=True, timeout=20,
        )
        for line in r.stdout.splitlines():
            if "api_gateway.py" in line:
                parts = line.split()
                for p in parts:
                    if p.isdigit():
                        pids.append(int(p))
    except Exception as e:
        print("wmic err:", e)
    return pids


def wait_port_open(port, timeout=30):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=2):
                return True
        except OSError:
            time.sleep(1)
    return False


def main():
    pids = find_gateway_pids()
    print("PID api_gateway trouvés:", pids)

    # Arrêt propre
    for pid in pids:
        try:
            subprocess.run(["taskkill", "/PID", str(pid), "/F"],
                           capture_output=True, text=True, timeout=15)
            print(f"  arrêté {pid}")
        except Exception as e:
            print(f"  erreur arrêt {pid}: {e}")

    time.sleep(3)

    # Relance en arrière-plan, détachée
    cmd = [sys.executable, str(BASE / "api_gateway.py"), "--port", "8000", "--host", "0.0.0.0"]
    proc = subprocess.Popen(
        cmd, cwd=str(BASE.parent),
        stdout=open(str(BASE / "api_gateway_restart.log"), "a", encoding="utf-8"),
        stderr=subprocess.STDOUT,
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS,
    )
    print(f"  relancé PID {proc.pid}")

    if wait_port_open(PORT, timeout=30):
        print("[OK] API Gateway de nouveau joignable sur :8000")
    else:
        print("[WARN] Port 8000 non ouvert après 30s — consulter api_gateway_restart.log")


if __name__ == "__main__":
    main()
