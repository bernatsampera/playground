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
CONTAINER_NAME = "l4k00sk4gs8s4gck04os08so-225946978914"
TMP_PATH_ON_REMOTE = "/root/workflows.db"
CONTAINER_DB_PATH = "/app/workflows.db"

def create_ssh_client():
    key = paramiko.RSAKey.from_private_key_file(SSH_KEY)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(REMOTE_HOST, username=REMOTE_USER, pkey=key)
    return client

# Method 1: Direct volume access (Recommended)
def download_db_from_volume():
    """Download database directly from Docker volume"""
    print("🔽 Downloading DB directly from volume...")
    ssh = create_ssh_client()
    
    # First, find the actual volume name
    stdin, stdout, stderr = ssh.exec_command("docker volume ls --format '{{.Name}}' | grep -E '(database|transcriptai|workflow)'")
    volumes = stdout.read().decode().strip().split('\n')
    print(f"📋 Available volumes: {volumes}")
    
    if volumes and volumes[0]:
        volume_name = volumes[0]
        volume_path = f"/var/lib/docker/volumes/{volume_name}/_data/database.db"
        
        # Check if database file exists in volume
        stdin, stdout, stderr = ssh.exec_command(f"ls -la {volume_path}")
        file_info = stdout.read().decode().strip()
        print(f"📋 Database file info: {file_info}")
        
        # Download directly from volume
        with SCPClient(ssh.get_transport()) as scp: # type: ignore
            scp.get(volume_path, LOCAL_PATH)
        
        print(f"✅ Downloaded from volume to: {LOCAL_PATH}")
    else:
        print("❌ No database volume found")
    
    ssh.close()

def upload_db_to_volume():
    """Upload database directly to Docker volume"""
    print("🔼 Uploading DB directly to volume...")
    if not os.path.exists(LOCAL_PATH):
        print(f"❌ Local file not found: {LOCAL_PATH}")
        return

    ssh = create_ssh_client()
    
    # Find volume name
    stdin, stdout, stderr = ssh.exec_command("docker volume ls --format '{{.Name}}' | grep -E '(database|transcriptai|workflow)'")
    volumes = stdout.read().decode().strip().split('\n')
    
    if volumes and volumes[0]:
        volume_name = volumes[0]
        volume_path = f"/var/lib/docker/volumes/{volume_name}/_data/database.db"
        
        # Upload directly to volume
        with SCPClient(ssh.get_transport()) as scp: # type: ignore
            scp.put(LOCAL_PATH, volume_path)
        
        # Set proper ownership (1000:1000 is typically the app user in containers)
        stdin, stdout, stderr = ssh.exec_command(f"chown 1000:1000 {volume_path}")
        stdin, stdout, stderr = ssh.exec_command(f"chmod 664 {volume_path}")
        
        print("✅ Uploaded directly to volume with proper permissions.")
    else:
        print("❌ No database volume found")
    
    ssh.close()

# Method 2: Via container (backup method)
def download_db_via_container():
    """Download database via container (fallback method)"""
    print("🔽 Downloading DB via container...")
    ssh = create_ssh_client()
    
    # Copy from container to host temp
    stdin, stdout, stderr = ssh.exec_command(
        f"docker cp {CONTAINER_NAME}:{CONTAINER_DB_PATH} {TMP_PATH_ON_REMOTE}"
    )
    stdout.channel.recv_exit_status()

    # Download from host to local
    with SCPClient(ssh.get_transport()) as scp: # type: ignore
        scp.get(TMP_PATH_ON_REMOTE, LOCAL_PATH)

    print(f"✅ Downloaded via container to: {LOCAL_PATH}")
    ssh.close()

def upload_db_via_container():
    """Upload database via container (fallback method)"""
    print("🔼 Uploading DB via container...")
    if not os.path.exists(LOCAL_PATH):
        print(f"❌ Local file not found: {LOCAL_PATH}")
        return

    ssh = create_ssh_client()
    
    # Upload to host temp
    with SCPClient(ssh.get_transport()) as scp: # type: ignore
        scp.put(LOCAL_PATH, TMP_PATH_ON_REMOTE)

    # Copy from host temp to container
    stdin, stdout, stderr = ssh.exec_command(
        f"docker cp {TMP_PATH_ON_REMOTE} {CONTAINER_NAME}:{CONTAINER_DB_PATH}"
    )
    stdout.channel.recv_exit_status()
    
    # Set proper permissions inside container
    stdin, stdout, stderr = ssh.exec_command(
        f"docker exec {CONTAINER_NAME} chown app:app {CONTAINER_DB_PATH}"
    )
    stdin, stdout, stderr = ssh.exec_command(
        f"docker exec {CONTAINER_NAME} chmod 664 {CONTAINER_DB_PATH}"
    )
    
    print("✅ Uploaded via container with proper permissions.")
    ssh.close()

def remove_db_from_volume():
    """Remove database directly from volume"""
    print("🗑️  Removing DB from volume...")
    confirm = input("⚠️  This will completely delete the database from production. Are you sure? (yes/no): ").strip().lower()
    
    if confirm != "yes":
        print("❌ Operation cancelled.")
        return
    
    try:
        ssh = create_ssh_client()
        
        # Find volume name
        stdin, stdout, stderr = ssh.exec_command("docker volume ls --format '{{.Name}}' | grep -E '(database|transcriptai|workflow)'")
        volumes = stdout.read().decode().strip().split('\n')
        
        if volumes and volumes[0]:
            volume_name = volumes[0]
            volume_path = f"/var/lib/docker/volumes/{volume_name}/_data/database.db"
            
            stdin, stdout, stderr = ssh.exec_command(f"rm -f {volume_path}")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                print("✅ Database successfully removed from volume.")
            else:
                error = stderr.read().decode().strip()
                print(f"❌ Failed to remove database: {error}")
        else:
            print("❌ No database volume found")
        
        ssh.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")

# Utility functions
def list_volumes():
    """List all Docker volumes on the server"""
    print("📋 Listing Docker volumes...")
    ssh = create_ssh_client()
    stdin, stdout, stderr = ssh.exec_command("docker volume ls")
    volumes = stdout.read().decode()
    print(volumes)
    ssh.close()

def inspect_volume():
    """Inspect the database volume"""
    print("🔍 Inspecting database volume...")
    ssh = create_ssh_client()
    
    stdin, stdout, stderr = ssh.exec_command("docker volume ls --format '{{.Name}}' | grep -E '(database|transcriptai|workflow)'")
    volumes = stdout.read().decode().strip().split('\n')
    
    if volumes and volumes[0]:
        volume_name = volumes[0]
        stdin, stdout, stderr = ssh.exec_command(f"docker volume inspect {volume_name}")
        volume_info = stdout.read().decode()
        print(volume_info)
        
        # Also check what's inside
        stdin, stdout, stderr = ssh.exec_command(f"ls -la /var/lib/docker/volumes/{volume_name}/_data/")
        contents = stdout.read().decode()
        print(f"\n📁 Volume contents:\n{contents}")
    
    ssh.close()

def backup_database():
    """Create a timestamped backup of the database"""
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"./database_backup_{timestamp}.db"
    
    print(f"💾 Creating backup: {backup_path}")
    ssh = create_ssh_client()
    
    stdin, stdout, stderr = ssh.exec_command("docker volume ls --format '{{.Name}}' | grep -E '(database|transcriptai|workflow)'")
    volumes = stdout.read().decode().strip().split('\n')
    
    if volumes and volumes[0]:
        volume_name = volumes[0]
        volume_path = f"/var/lib/docker/volumes/{volume_name}/_data/database.db"
        
        with SCPClient(ssh.get_transport()) as scp: # type: ignore
            scp.get(volume_path, backup_path)
        
        print(f"✅ Backup created: {backup_path}")
    
    ssh.close()

# Main interface
def main():
    print("🗄️  Database Management Tool")
    print("1. Download database from volume")
    print("2. Upload database to volume") 
    print("3. Download via container (fallback)")
    print("4. Upload via container (fallback)")
    print("5. Remove database")
    print("6. List volumes")
    print("7. Inspect volume")
    print("8. Create backup")
    
    choice = input("\nSelect option (1-8): ").strip()
    
    if choice == "1":
        download_db_from_volume()
    elif choice == "2":
        upload_db_to_volume()
    elif choice == "3":
        download_db_via_container()
    elif choice == "4":
        upload_db_via_container()
    elif choice == "5":
        remove_db_from_volume()
    elif choice == "6":
        list_volumes()
    elif choice == "7":
        inspect_volume()
    elif choice == "8":
        backup_database()
    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main()