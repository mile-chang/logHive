# Database Models for LogHive
import sqlite3
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from config import get_database_path, USERS_CONFIG


def get_db_connection(environment='production'):
    """Get database connection with row factory based on environment"""
    db_path = get_database_path(environment)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize database tables for both test and production environments"""
    for env in ['test', 'production']:
        conn = get_db_connection(env)
        cursor = conn.cursor()
        
        # Users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                environment TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Disk usage records table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS disk_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                site TEXT NOT NULL,
                sub_site TEXT NOT NULL,
                server_type TEXT NOT NULL,
                path TEXT NOT NULL,
                size_mb REAL NOT NULL,
                recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_disk_usage_lookup 
            ON disk_usage (site, sub_site, server_type, recorded_at)
        ''')
        
        conn.commit()
        
        # Create users for this environment (only if they don't exist)
        for user_key, user_config in USERS_CONFIG.items():
            if user_config['environment'] == env:
                cursor.execute('SELECT id FROM users WHERE username = ?', (user_config['username'],))
                if not cursor.fetchone():
                    # User doesn't exist, create new one
                    password_hash = generate_password_hash(user_config['password'])
                    cursor.execute(
                        'INSERT INTO users (username, password_hash, environment) VALUES (?, ?, ?)',
                        (user_config['username'], password_hash, user_config['environment'])
                    )
                    conn.commit()
        
        conn.close()


class User:
    """User model for authentication"""
    
    def __init__(self, id, username, environment='production'):
        self.id = id
        self.username = username
        self.environment = environment
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
    
    def get_id(self):
        return str(self.id)
    
    @staticmethod
    def get_by_id(user_id):
        # Try both environments
        for env in ['test', 'production']:
            conn = get_db_connection(env)
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, environment FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return User(row['id'], row['username'], row['environment'])
        return None
    
    @staticmethod
    def get_by_username(username):
        # Try both environments
        for env in ['test', 'production']:
            conn = get_db_connection(env)
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, environment FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return User(row['id'], row['username'], row['environment'])
        return None
    
    @staticmethod
    def verify_password(username, password):
        # Try both environments
        for env in ['test', 'production']:
            conn = get_db_connection(env)
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, password_hash, environment FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()
            if row and check_password_hash(row['password_hash'], password):
                return User(row['id'], row['username'], row['environment'])
        return None


class DiskUsage:
    """Disk usage record model"""
    
    @staticmethod
    def record(site, sub_site, server_type, path, size_mb, environment='production'):
        """Record a new disk usage entry"""
        conn = get_db_connection(environment)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO disk_usage (site, sub_site, server_type, path, size_mb)
            VALUES (?, ?, ?, ?, ?)
        ''', (site, sub_site, server_type, path, size_mb))
        conn.commit()
        conn.close()
    
    @staticmethod
    def get_latest(site, sub_site, server_type, environment='production'):
        """Get the latest disk usage record"""
        conn = get_db_connection(environment)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT size_mb, recorded_at FROM disk_usage
            WHERE site = ? AND sub_site = ? AND server_type = ?
            ORDER BY recorded_at DESC
            LIMIT 1
        ''', (site, sub_site, server_type))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {'size_mb': row['size_mb'], 'recorded_at': row['recorded_at']}
        return None
    
    @staticmethod
    def get_history(site, sub_site, server_type, days=30, environment='production'):
        """Get disk usage history for the past N days"""
        conn = get_db_connection(environment)
        cursor = conn.cursor()
        since = datetime.now() - timedelta(days=days)
        cursor.execute('''
            SELECT size_mb, recorded_at FROM disk_usage
            WHERE site = ? AND sub_site = ? AND server_type = ?
            AND recorded_at >= ?
            ORDER BY recorded_at ASC
        ''', (site, sub_site, server_type, since.isoformat()))
        rows = cursor.fetchall()
        conn.close()
        return [{'size_mb': row['size_mb'], 'recorded_at': row['recorded_at']} for row in rows]
    
    @staticmethod
    def get_monthly_growth(site, sub_site, server_type, environment='production'):
        """Calculate monthly growth statistics"""
        conn = get_db_connection(environment)
        cursor = conn.cursor()
        
        # Get data grouped by month
        cursor.execute('''
            SELECT 
                strftime('%Y-%m', recorded_at) as month,
                MIN(size_mb) as min_size,
                MAX(size_mb) as max_size
            FROM disk_usage
            WHERE site = ? AND sub_site = ? AND server_type = ?
            GROUP BY month
            ORDER BY month DESC
            LIMIT 12
        ''', (site, sub_site, server_type))
        
        rows = cursor.fetchall()
        conn.close()
        
        monthly_data = []
        for row in rows:
            growth = row['max_size'] - row['min_size']
            monthly_data.append({
                'month': row['month'],
                'growth_mb': growth,
                'max_size_mb': row['max_size']
            })
        
        return monthly_data
    
    @staticmethod
    def get_current_and_previous_month_growth(site, sub_site, server_type, environment='production'):
        """Get current month and previous month growth"""
        conn = get_db_connection(environment)
        cursor = conn.cursor()
        
        now = datetime.now()
        current_month = now.strftime('%Y-%m')
        
        # Calculate previous month
        if now.month == 1:
            prev_month = f"{now.year - 1}-12"
        else:
            prev_month = f"{now.year}-{now.month - 1:02d}"
        
        # Get current month growth
        cursor.execute('''
            SELECT MIN(size_mb) as min_size, MAX(size_mb) as max_size
            FROM disk_usage
            WHERE site = ? AND sub_site = ? AND server_type = ?
            AND strftime('%Y-%m', recorded_at) = ?
        ''', (site, sub_site, server_type, current_month))
        current = cursor.fetchone()
        current_growth = (current['max_size'] - current['min_size']) if current and current['min_size'] else 0
        
        # Get previous month growth
        cursor.execute('''
            SELECT MIN(size_mb) as min_size, MAX(size_mb) as max_size
            FROM disk_usage
            WHERE site = ? AND sub_site = ? AND server_type = ?
            AND strftime('%Y-%m', recorded_at) = ?
        ''', (site, sub_site, server_type, prev_month))
        previous = cursor.fetchone()
        previous_growth = (previous['max_size'] - previous['min_size']) if previous and previous['min_size'] else 0
        
        conn.close()
        
        return {
            'current_month': current_month,
            'current_month_growth': current_growth,
            'previous_month': prev_month,
            'previous_month_growth': previous_growth
        }
    
    @staticmethod
    def get_30day_growth(site, sub_site, server_type, environment='production'):
        """Calculate growth in the last 30 days"""
        conn = get_db_connection(environment)
        cursor = conn.cursor()
        
        now = datetime.now()
        thirty_days_ago = now - timedelta(days=30)
        
        # Get earliest record in last 30 days
        cursor.execute('''
            SELECT size_mb FROM disk_usage
            WHERE site = ? AND sub_site = ? AND server_type = ?
            AND recorded_at >= ?
            ORDER BY recorded_at ASC
            LIMIT 1
        ''', (site, sub_site, server_type, thirty_days_ago.isoformat()))
        earliest = cursor.fetchone()
        
        # Get latest record
        cursor.execute('''
            SELECT size_mb FROM disk_usage
            WHERE site = ? AND sub_site = ? AND server_type = ?
            ORDER BY recorded_at DESC
            LIMIT 1
        ''', (site, sub_site, server_type))
        latest = cursor.fetchone()
        
        conn.close()
        
        if earliest and latest:
            return latest['size_mb'] - earliest['size_mb']
        return 0
    
    @staticmethod
    def get_all_sites_summary(environment='production'):
        """Get summary for all sites and servers"""
        conn = get_db_connection(environment)
        cursor = conn.cursor()
        
        # Get latest record for each site/sub_site/server combination
        cursor.execute('''
            SELECT 
                d1.site, d1.sub_site, d1.server_type, d1.size_mb, d1.recorded_at
            FROM disk_usage d1
            INNER JOIN (
                SELECT site, sub_site, server_type, MAX(recorded_at) as max_recorded
                FROM disk_usage
                GROUP BY site, sub_site, server_type
            ) d2 ON d1.site = d2.site 
                AND d1.sub_site = d2.sub_site 
                AND d1.server_type = d2.server_type 
                AND d1.recorded_at = d2.max_recorded
            ORDER BY d1.site, d1.sub_site, d1.server_type
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            'site': row['site'],
            'sub_site': row['sub_site'],
            'server_type': row['server_type'],
            'size_mb': row['size_mb'],
            'recorded_at': row['recorded_at']
        } for row in rows]
