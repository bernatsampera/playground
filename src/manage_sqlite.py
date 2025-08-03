import os
import paramiko
from scp import SCPClient
import hashlib
import sqlite3

# === Configuration ===
SSH_KEY = os.path.expanduser("~/.ssh/hetzni")
REMOTE_HOST = "178.156.132.116"
REMOTE_USER = "root"
LOCAL_PATH = os.path.abspath("./workflows.db")
CONTAINER_NAME = "l4k00sk4gs8s4gck04os08so-214817981839"
TMP_PATH_ON_REMOTE = "/root/workflows.db"
CONTAINER_DB_PATH = "/app/workflows.db"

def create_ssh_client():
    key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(REMOTE_HOST, username=REMOTE_USER, pkey=key)
    return client

def download_db():
    print("🔽 Downloading DB from container...")
    ssh = create_ssh_client()
    stdin, stdout, stderr = ssh.exec_command(
        f"docker cp {CONTAINER_NAME}:{CONTAINER_DB_PATH} {TMP_PATH_ON_REMOTE}"
    )
    stdout.channel.recv_exit_status()

    with SCPClient(ssh.get_transport()) as scp: # type: ignore
        scp.get(TMP_PATH_ON_REMOTE, LOCAL_PATH)

    print(f"✅ Downloaded to: {LOCAL_PATH}")
    ssh.close()

def upload_db():
    print("🔼 Uploading DB to container...")
    if not os.path.exists(LOCAL_PATH):
        print(f"❌ Local file not found: {LOCAL_PATH}")
        return

    ssh = create_ssh_client()
    with SCPClient(ssh.get_transport()) as scp: # type: ignore
        scp.put(LOCAL_PATH, TMP_PATH_ON_REMOTE)

    stdin, stdout, stderr = ssh.exec_command(
        f"docker cp {TMP_PATH_ON_REMOTE} {CONTAINER_NAME}:{CONTAINER_DB_PATH}"
    )
    stdout.channel.recv_exit_status()
    print("✅ Uploaded and replaced inside container.")
    ssh.close()

def create_user():
    print("👤 Create New User")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()
    
    if not username or not password:
        print("❌ Username and password cannot be empty.")
        return
    
    # Hash the password using the same method as the app
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        # Connect to the local database
        conn = sqlite3.connect(LOCAL_PATH)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print("❌ User already exists.")
            conn.close()
            return
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
        print(f"✅ User '{username}' created successfully!")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")

def remove_db():
    print("🗑️  Removing DB from container...")
    confirm = input("⚠️  This will completely delete the database from production. Are you sure? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Operation cancelled.")
        return
    
    try:
        ssh = create_ssh_client()
        stdin, stdout, stderr = ssh.exec_command(
            f"docker exec {CONTAINER_NAME} rm -f {CONTAINER_DB_PATH}"
        )
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status == 0:
            print("✅ Database successfully removed from container.")
        else:
            error = stderr.read().decode().strip()
            print(f"❌ Failed to remove database: {error}")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def list_containers():
    print("📋 Listing running containers...")
    try:
        ssh = create_ssh_client()
        stdin, stdout, stderr = ssh.exec_command("docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}'")
        containers = stdout.read().decode().strip()
        error = stderr.read().decode().strip()
        
        if containers:
            print("Running containers:")
            print(containers)
        else:
            print("No running containers found.")
            
        if error:
            print(f"Error: {error}")
            
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    print("=== Manage SQLite DB ===")
    print("1. Download from container")
    print("2. Upload to container")
    print("3. Create user")
    print("4. Remove DB from container")
    print("5. List containers")
    print("6. Exit")
    choice = input("Choose an option: ").strip()

    if choice == "1":
        download_db()
    elif choice == "2":
        upload_db()
    elif choice == "3":
        create_user()
    elif choice == "4":
        remove_db()
    elif choice == "5":
        list_containers()
    elif choice == "6":
        print("Bye!")
    else:
        print("❌ Invalid choice.")

if __name__ == "__main__":
    main()
