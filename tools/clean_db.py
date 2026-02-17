"""
Clean and reinitialize databases
This will remove existing databases and create fresh ones
"""
import os
from config import get_database_path
from models import init_db

def clean_and_init():
    """Remove old databases and create fresh ones"""
    
    # Remove old databases
    for env in ['production', 'test']:
        db_path = get_database_path(env)
        if os.path.exists(db_path):
            print(f"Removing old {env} database: {db_path}")
            os.remove(db_path)
        else:
            print(f"No existing {env} database found")
    
    print("\nCreating fresh databases...")
    init_db()
    print("Databases initialized successfully!")
    
    # Verify created databases
    print("\nVerifying databases:")
    for env in ['production', 'test']:
        db_path = get_database_path(env)
        if os.path.exists(db_path):
            print(f"  ✓ {env}: {db_path}")
        else:
            print(f"  ✗ {env}: NOT FOUND")

if __name__ == '__main__':
    response = input("This will DELETE all existing data. Continue? (yes/no): ")
    if response.lower() == 'yes':
        clean_and_init()
    else:
        print("Operation cancelled")
