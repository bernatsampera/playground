#!/usr/bin/env python3
"""
TablePlus Database Sync Script
Keeps a local copy of the remote database in sync for TablePlus access
"""

import os
import time
import paramiko
from scp import SCPClient
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import argparse
import hashlib

# Configuration
SERVER_IP = "178.156.132.116"  # Your server IP
SSH_KEY_PATH = "~/.ssh/hetzni"
LOCAL_DB_PATH = "./local_workflows.db"
SYNC_INTERVAL = 30  # seconds

class DatabaseSyncHandler(FileSystemEventHandler):
    def __init__(self, sync_manager):
        self.sync_manager = sync_manager
        self.last_upload = 0
        self.pending_changes = False
    
    def on_modified(self, event):
        if event.src_path.endswith('.db') and time.time() - self.last_upload > 2: # type: ignore
            print("🔄 Local database changed, marking for upload...")
            self.pending_changes = True
            self.last_upload = time.time()
            # Upload immediately
            self.sync_manager.upload_to_server()
            self.pending_changes = False

class DatabaseSyncManager:
    def __init__(self):
        self.ssh_key_path = os.path.expanduser(SSH_KEY_PATH)
        self.running = False
        self.volume_name = None
        self.last_local_hash = None
        self.last_server_hash = None
        
    def get_file_hash(self, file_path):
        """Get MD5 hash of a file"""
        if not os.path.exists(file_path):
            return None
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def get_server_file_hash(self):
        """Get MD5 hash of the server database file"""
        try:
            ssh = self.create_ssh_client()
            remote_path = self.get_remote_db_path()
            
            # Check if remote file exists
            stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_path} && echo 'exists' || echo 'not found'")
            result = stdout.read().decode().strip()
            
            if result == "not found":
                ssh.close()
                return None
            
            # Get MD5 hash of remote file
            stdin, stdout, stderr = ssh.exec_command(f"md5sum {remote_path}")
            hash_result = stdout.read().decode().strip()
            ssh.close()
            
            if hash_result:
                return hash_result.split()[0]
            return None
            
        except Exception as e:
            print(f"❌ Failed to get server file hash: {e}")
            return None
    
    def create_ssh_client(self):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(
            hostname=SERVER_IP,
            username="root",
            key_filename=self.ssh_key_path
        )
        return ssh
    
    def find_volume_name(self):
        """Find the database volume name"""
        if self.volume_name:
            return self.volume_name
            
        ssh = self.create_ssh_client()
        stdin, stdout, stderr = ssh.exec_command(
            "docker volume ls --format '{{.Name}}' | grep -E '(database|transcriptai|workflow)'"
        )
        volumes = stdout.read().decode().strip().split('\n')
        ssh.close()
        
        if volumes and volumes[0]:
            self.volume_name = volumes[0]
            print(f"📋 Found volume: {self.volume_name}")
            return self.volume_name
        else:
            raise Exception("No database volume found")
    
    def get_remote_db_path(self):
        """Get the full path to the database on the server"""
        volume_name = self.find_volume_name()
        return f"/var/lib/docker/volumes/{volume_name}/_data/workflows.db"
    
    def download_from_server(self):
        """Download database from server to local file"""
        try:
            ssh = self.create_ssh_client()
            remote_path = self.get_remote_db_path()
            
            # Check if remote file exists
            stdin, stdout, stderr = ssh.exec_command(f"test -f {remote_path} && echo 'exists' || echo 'not found'")
            result = stdout.read().decode().strip()
            
            if result == "not found":
                print("⚠️  Remote database file not found")
                ssh.close()
                return False
            
            with SCPClient(ssh.get_transport()) as scp: # type: ignore
                scp.get(remote_path, LOCAL_DB_PATH)
            
            ssh.close()
            print(f"⬇️  Downloaded database to {LOCAL_DB_PATH}")
            return True
            
        except Exception as e:
            print(f"❌ Download failed: {e}")
            return False
    
    def upload_to_server(self):
        """Upload local database to server"""
        if not os.path.exists(LOCAL_DB_PATH):
            print("❌ Local database file not found")
            return False
            
        try:
            ssh = self.create_ssh_client()
            remote_path = self.get_remote_db_path()
            
            with SCPClient(ssh.get_transport()) as scp: # type: ignore  
                scp.put(LOCAL_DB_PATH, remote_path)
            
            # Fix permissions
            stdin, stdout, stderr = ssh.exec_command(f"chown 1000:1000 {remote_path}")
            stdin, stdout, stderr = ssh.exec_command(f"chmod 664 {remote_path}")
            
            ssh.close()
            print(f"⬆️  Uploaded database to server")
            return True
            
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return False
    
    def watch_local_changes(self):
        """Watch for local file changes and auto-upload"""
        event_handler = DatabaseSyncHandler(self)
        observer = Observer()
        observer.schedule(event_handler, os.path.dirname(os.path.abspath(LOCAL_DB_PATH)), recursive=False)
        observer.start()
        
        print(f"👀 Watching {LOCAL_DB_PATH} for changes...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            observer.stop()
            observer.join()
    
    def sync_periodically(self):
        """Periodically sync from server with conflict detection"""
        while self.running:
            time.sleep(SYNC_INTERVAL)
            if not self.running:
                break
                
            print("🔄 Checking for server changes...")
            
            # Get current hashes
            current_local_hash = self.get_file_hash(LOCAL_DB_PATH)
            current_server_hash = self.get_server_file_hash()
            
            if current_server_hash is None:
                print("⚠️  Could not get server file hash, skipping sync")
                continue
            
            # If we have no previous hashes, this is the first sync
            if self.last_local_hash is None or self.last_server_hash is None:
                print("📥 First sync - downloading from server...")
                self.download_from_server()
                self.last_local_hash = current_local_hash
                self.last_server_hash = current_server_hash
                continue
            
            # Check if local has changed since our last sync
            if current_local_hash != self.last_local_hash:
                print("🔄 Local database has changed, uploading to server...")
                self.upload_to_server()
                self.last_local_hash = current_local_hash
                self.last_server_hash = self.get_server_file_hash()
                continue
            
            # Check if server has changed since our last sync
            if current_server_hash != self.last_server_hash:
                print("🔄 Server database has changed")
                
                # Check if local has also changed since our last sync
                if current_local_hash != self.last_local_hash:
                    print("⚠️  Both local and server have changed - uploading local changes to server...")
                    self.upload_to_server()
                    self.last_local_hash = current_local_hash
                    self.last_server_hash = self.get_server_file_hash()
                else:
                    print("📥 Server changed, downloading updates...")
                    self.download_from_server()
                    self.last_local_hash = self.get_file_hash(LOCAL_DB_PATH)
                    self.last_server_hash = current_server_hash
            else:
                print("✅ No changes detected")
    
    def start_sync(self, watch_changes=True, periodic_sync=True):
        """Start the sync process"""
        print("🚀 Starting database sync...")
        print(f"📍 Server: {SERVER_IP}")
        print(f"📁 Local DB: {LOCAL_DB_PATH}")
        
        # Initial download
        if not self.download_from_server():
            print("⚠️  Initial download failed, but continuing...")
        
        # Initialize hash tracking
        self.last_local_hash = self.get_file_hash(LOCAL_DB_PATH)
        self.last_server_hash = self.get_server_file_hash()
        
        self.running = True
        
        threads = []
        
        if watch_changes:
            watch_thread = threading.Thread(target=self.watch_local_changes)
            watch_thread.daemon = True
            watch_thread.start()
            threads.append(watch_thread)
        
        if periodic_sync:
            sync_thread = threading.Thread(target=self.sync_periodically)
            sync_thread.daemon = True
            sync_thread.start()
            threads.append(sync_thread)
        
        print("\n✅ Sync started! You can now:")
        print(f"   1. Open {LOCAL_DB_PATH} in TablePlus")
        print("   2. Make changes in TablePlus")
        print("   3. Changes will auto-upload to server")
        print("   4. Server changes will only sync if no local conflicts")
        print("\nPress Ctrl+C to stop...")
        
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Stopping sync...")
            self.running = False
            
            for thread in threads:
                thread.join(timeout=2)

def main():
    parser = argparse.ArgumentParser(description="Database sync for TablePlus")
    parser.add_argument("--download-only", action="store_true", help="Just download once and exit")
    parser.add_argument("--upload-only", action="store_true", help="Just upload once and exit")
    parser.add_argument("--no-watch", action="store_true", help="Don't watch for local changes")
    parser.add_argument("--no-periodic", action="store_true", help="Don't periodically sync from server")
    
    args = parser.parse_args()
    
    sync_manager = DatabaseSyncManager()
    
    if args.download_only:
        sync_manager.download_from_server()
        print(f"✅ Database downloaded to {LOCAL_DB_PATH}")
        print("You can now open this file in TablePlus")
        return
    
    if args.upload_only:
        if sync_manager.upload_to_server():
            print("✅ Database uploaded to server")
        return
    
    # Start full sync
    sync_manager.start_sync(
        watch_changes=not args.no_watch,
        periodic_sync=not args.no_periodic
    )

if __name__ == "__main__":
    main()