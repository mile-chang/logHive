"""
Database migration script to add environment column to existing databases
"""
import sqlite3
import os
from config import get_database_path, USERS_CONFIG
from werkzeug.security import generate_password_hash

def migrate_database(environment):
    """Add environment column to users table if it doesn't exist"""
    db_path = get_database_path(environment)
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} does not exist. Skipping migration.")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if environment column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    if 'environment' not in columns:
        print(f"Adding environment column to {environment} database...")
        
        # Add environment column with default value
        cursor.execute("ALTER TABLE users ADD COLUMN environment TEXT NOT NULL DEFAULT 'production'")
        
        # Update existing users with correct environment
        for user_key, user_config in USERS_CONFIG.items():
            if user_config['environment'] == environment:
                cursor.execute(
                    "UPDATE users SET environment = ? WHERE username = ?",
                    (user_config['environment'], user_config['username'])
                )
        
        conn.commit()
        print(f"Migration complete for {environment} database")
    else:
        print(f"Environment column already exists in {environment} database")
    
    # Ensure users exist for this environment
    for user_key, user_config in USERS_CONFIG.items():
        if user_config['environment'] == environment:
            cursor.execute('SELECT id FROM users WHERE username = ?', (user_config['username'],))
            if not cursor.fetchone():
                print(f"Creating user {user_config['username']} in {environment} database...")
                password_hash = generate_password_hash(user_config['password'])
                cursor.execute(
                    'INSERT INTO users (username, password_hash, environment) VALUES (?, ?, ?)',
                    (user_config['username'], password_hash, user_config['environment'])
                )
                conn.commit()
                print(f"User {user_config['username']} created")
    
    conn.close()

if __name__ == '__main__':
    print("Running database migration...")
    migrate_database('production')
    migrate_database('test')
    print("Migration complete!")
