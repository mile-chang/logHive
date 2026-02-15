#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Update user passwords from .env without losing database data

import os
import sys
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash
from models import get_db_connection

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

print("=" * 60)
print("Update User Passwords from .env")
print("=" * 60)

# Load .env file
print("\n[1] Loading .env file...")
load_dotenv()
print("OK - Environment variables loaded")

# Get passwords from environment
admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
test_password = os.environ.get('TEST_PASSWORD', 'test123')
admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
test_username = os.environ.get('TEST_USERNAME', 'test')

print(f"\n[2] Will update passwords for:")
print(f"  - {admin_username} (production)")
print(f"  - {test_username} (test)")

# Update production admin password
print("\n[3] Updating production database...")
try:
    conn = get_db_connection('production')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id, username FROM users WHERE username = ?', (admin_username,))
    user = cursor.fetchone()
    
    if user:
        # Update password
        password_hash = generate_password_hash(admin_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                      (password_hash, admin_username))
        conn.commit()
        print(f"OK - Updated password for '{admin_username}' in production database")
    else:
        print(f"WARNING - User '{admin_username}' not found in production database")
        print(f"         Creating new user...")
        password_hash = generate_password_hash(admin_password)
        cursor.execute(
            'INSERT INTO users (username, password_hash, environment) VALUES (?, ?, ?)',
            (admin_username, password_hash, 'production')
        )
        conn.commit()
        print(f"OK - Created user '{admin_username}' in production database")
    
    conn.close()
except Exception as e:
    print(f"ERROR - Failed to update production database: {e}")

# Update test database password
print("\n[4] Updating test database...")
try:
    conn = get_db_connection('test')
    cursor = conn.cursor()
    
    # Check if user exists
    cursor.execute('SELECT id, username FROM users WHERE username = ?', (test_username,))
    user = cursor.fetchone()
    
    if user:
        # Update password
        password_hash = generate_password_hash(test_password)
        cursor.execute('UPDATE users SET password_hash = ? WHERE username = ?', 
                      (password_hash, test_username))
        conn.commit()
        print(f"OK - Updated password for '{test_username}' in test database")
    else:
        print(f"WARNING - User '{test_username}' not found in test database")
        print(f"         Creating new user...")
        password_hash = generate_password_hash(test_password)
        cursor.execute(
            'INSERT INTO users (username, password_hash, environment) VALUES (?, ?, ?)',
            (test_username, password_hash, 'test')
        )
        conn.commit()
        print(f"OK - Created user '{test_username}' in test database")
    
    conn.close()
except Exception as e:
    print(f"ERROR - Failed to update test database: {e}")

print("\n" + "=" * 60)
print("Password update complete!")
print("=" * 60)
print("\nYou can now login with:")
print(f"  Production: {admin_username} / (password from .env)")
print(f"  Test:       {test_username} / (password from .env)")
print("=" * 60)
