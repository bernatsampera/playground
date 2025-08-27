#!/usr/bin/env python3
"""
User Management Tool for Workflows Database
Adds users to the local database that syncs with the server
"""

import sqlite3
import datetime
import hashlib
import os

# Configuration - same as tunneldb.py
LOCAL_DB_PATH = "./local_workflows.db"

def hash_password(password):
    """Hash a password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user(username, password, max_calls_per_month=50):
    """Add a new user to the database"""
    if not os.path.exists(LOCAL_DB_PATH):
        print(f"❌ Database file not found: {LOCAL_DB_PATH}")
        print("💡 Make sure to run the tunnel sync first to download the database")
        return False
    
    try:
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cursor = conn.cursor()
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            print(f"❌ User '{username}' already exists")
            return False
        
        # Hash the password
        hashed_password = hash_password(password)
        
        # Get current timestamp
        created_at = datetime.datetime.now().isoformat()
        
        # Insert new user
        cursor.execute("""
            INSERT INTO users (username, password, max_calls_per_month, created_at)
            VALUES (?, ?, ?, ?)
        """, (username, hashed_password, max_calls_per_month, created_at))
        
        conn.commit()
        conn.close()
        
        print(f"✅ User '{username}' added successfully!")
        print(f"   Max calls per month: {max_calls_per_month}")
        print(f"   Created at: {created_at}")
        print("\n💡 Remember to run the tunnel sync to upload changes to the server")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def list_users():
    """List all users in the database"""
    if not os.path.exists(LOCAL_DB_PATH):
        print(f"❌ Database file not found: {LOCAL_DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(LOCAL_DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT id, username, max_calls_per_month, created_at FROM users ORDER BY id")
        users = cursor.fetchall()
        
        conn.close()
        
        if not users:
            print("📋 No users found in database")
            return True
        
        print("📋 Users in database:")
        print("-" * 60)
        print(f"{'ID':<3} {'Username':<20} {'Max Calls':<10} {'Created At'}")
        print("-" * 60)
        
        for user in users:
            user_id, username, max_calls, created_at = user
            # Truncate created_at for display
            created_display = created_at[:19] if created_at else "N/A"
            print(f"{user_id:<3} {username:<20} {max_calls:<10} {created_display}")
        
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False

def main():
    print("👤 User Management Tool")
    print("1. Add new user")
    print("2. List all users")
    
    choice = input("\nSelect option (1-2): ").strip()
    
    if choice == "1":
        username = input("Enter username: ").strip()
        if not username:
            print("❌ Username cannot be empty")
            return
        
        password = input("Enter password: ").strip()
        if not password:
            print("❌ Password cannot be empty")
            return
        
        max_calls_input = input("Enter max calls per month (default 50): ").strip()
        max_calls = 50
        if max_calls_input:
            try:
                max_calls = int(max_calls_input)
                if max_calls < 0:
                    print("❌ Max calls cannot be negative, using default 50")
                    max_calls = 50
            except ValueError:
                print("❌ Invalid number, using default 50")
        
        add_user(username, password, max_calls)
        
    elif choice == "2":
        list_users()
        
    else:
        print("❌ Invalid option")

if __name__ == "__main__":
    main()