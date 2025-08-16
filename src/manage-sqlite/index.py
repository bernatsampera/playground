import subprocess
import sys
import os

# Config
SSH_USER = "root"
SSH_HOST = "178.156.132.116"
SSH_KEY = os.path.expanduser("~/.ssh/hetzni")
REMOTE_DB_PATH = "/var/lib/docker/volumes/samperalabvolume/_data/content.db"
current_dir = os.path.dirname(os.path.abspath(__file__))
LOCAL_DB_PATH = os.path.join(current_dir, "content.db")

def pull_db():
    """Download the DB from the VPS to local machine."""
    print(f"Downloading {REMOTE_DB_PATH} from {SSH_HOST} → {LOCAL_DB_PATH}")
    subprocess.run([
        "scp",
        "-i", SSH_KEY,
        f"{SSH_USER}@{SSH_HOST}:{REMOTE_DB_PATH}",
        LOCAL_DB_PATH
    ], check=True)
    print("✅ Download complete.")

def push_db():
    """Upload the local DB back to the VPS."""
    if not os.path.exists(LOCAL_DB_PATH):
        print(f"❌ Local DB not found: {LOCAL_DB_PATH}")
        sys.exit(1)
    print(f"Uploading {LOCAL_DB_PATH} → {REMOTE_DB_PATH} on {SSH_HOST}")
    subprocess.run([
        "scp",
        "-i", SSH_KEY,
        LOCAL_DB_PATH,
        f"{SSH_USER}@{SSH_HOST}:{REMOTE_DB_PATH}"
    ], check=True)
    print("✅ Upload complete.")

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["pull", "push"]:
        print("Usage: python sync_sqlite.py [pull|push]")
        sys.exit(1)

    if sys.argv[1] == "pull":
        pull_db()
    else:
        push_db()
