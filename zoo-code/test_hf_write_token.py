import socket
import sys

socket.setdefaulttimeout(30)

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from huggingface_hub import HfApi

TOKEN = sys.argv[1] if len(sys.argv) > 1 else ""

api = HfApi(token=TOKEN)
try:
    who = api.whoami()
    print("WHOAMI", who["name"])
except Exception as e:
    print("WHOAMI_ERR", type(e).__name__, str(e)[:200])
    sys.exit(1)

# Teste un vrai upload d'un fichier test sur le dataset cible
test_content = "# Test write access\n\nprobe from publish_phase5_hf\n"
try:
    api.upload_file(
        path_or_fileobj=test_content.encode("utf-8"),
        path_in_repo="_probe_write_access.txt",
        repo_id="girard444/mttv-energy-flow-optimization",
        repo_type="dataset",
    )
    print("WRITE_TEST OK")
    # Nettoyage du fichier probe
    api.delete_file(
        path_in_repo="_probe_write_access.txt",
        repo_id="girard444/mttv-energy-flow-optimization",
        repo_type="dataset",
    )
    print("PROBE_CLEANED")
except Exception as e:
    print("WRITE_TEST_ERR", type(e).__name__, str(e)[:300])
    sys.exit(1)
