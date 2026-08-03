import re
import socket
import sys

socket.setdefaulttimeout(15)


def read_hf_token(path):
    raw = None
    for enc in ("utf-8", "latin-1", "cp1252"):
        try:
            with open(path, encoding=enc) as f:
                raw = f.read()
            break
        except UnicodeDecodeError:
            continue
    if raw is None:
        return ""
    m = re.search(r"^HF_TOKEN=(.+)$", raw, re.M)
    return m.group(1).strip() if m else ""


def main():
    token = read_hf_token("zoo-code/.env.tokens")
    if not token:
        print("NO_TOKEN")
        return
    print("TOKEN_PREFIX", token[:8], "LEN", len(token))
    from huggingface_hub import HfApi
    api = HfApi(token=token)
    try:
        who = api.whoami()
        print("WHOAMI", who["name"])
    except Exception as e:
        print("WHOAMI_ERR", type(e).__name__, str(e)[:200])
    # Vérifier les droits sur le dataset cible
    try:
        info = api.dataset_info("girard444/mttv-energy-flow-optimization")
        print("DATASET_INFO", info.id, "canWrite:", info.can_write if hasattr(info, "can_write") else "?")
    except Exception as e:
        print("DATASET_ERR", type(e).__name__, str(e)[:200])


if __name__ == "__main__":
    main()
