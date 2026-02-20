# LogHive - Main Flask Application
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import init_db, User, DiskUsage
from config import SECRET_KEY, SESSION_LIFETIME, API_TOKEN, SITES_CONFIG, ENVIRONMENT, PORT

# Prometheus metrics
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import Counter

app = Flask(__name__)
app.secret_key = SECRET_KEY
app.config['PERMANENT_SESSION_LIFETIME'] = SESSION_LIFETIME

# Initialize Prometheus metrics
metrics = PrometheusMetrics(app)

# Custom metrics
agent_reports_counter = Counter(
    'loghive_agent_reports_total',
    'Total number of agent disk usage reports received',
    ['site', 'sub_site', 'server_type']
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = None  # Don't flash message on redirect


@login_manager.user_loader
def load_user(user_id):
    # Get user environment from session
    user_env = session.get('user_environment', 'production')
    # Load user from the correct database
    conn_env = user_env
    for env in [conn_env, 'test' if conn_env == 'production' else 'production']:
        from models import get_db_connection
        conn = get_db_connection(env)
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, environment FROM users WHERE id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return User(row['id'], row['username'], row['environment'])
    return None


# ==================== Web Routes ====================

@app.route('/')
@login_required
def index():
    """Main dashboard page"""
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    return render_template('dashboard.html', sites_config=SITES_CONFIG, environment=user_env)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '')
        password = request.form.get('password', '')
        
        user = User.verify_password(username, password)
        if user:
            # Store user environment in session
            session['user_environment'] = user.environment
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('帳號或密碼錯誤', 'error')
    
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """Logout"""
    session.pop('user_environment', None)
    logout_user()
    return redirect(url_for('login'))


# ==================== API Routes ====================

@app.route('/api/report', methods=['POST'])
def api_report():
    """
    Receive disk usage report from agents
    Expected JSON:
    {
        "token": "api-token",
        "site": "Site_A",
        "sub_site": "WMX",
        "server_type": "log_server",
        "path": "/data",
        "size_mb": 1024.5
    }
    """
    data = request.get_json()
    
    # Validate token
    if not data or data.get('token') != API_TOKEN:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Validate required fields
    required = ['site', 'sub_site', 'server_type', 'path', 'size_mb']
    for field in required:
        if field not in data:
            return jsonify({'error': f'Missing field: {field}'}), 400
    
    try:
        size_mb = float(data['size_mb'])
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid size_mb value'}), 400
    
    # Record the data
    DiskUsage.record(
        site=data['site'],
        sub_site=data['sub_site'],
        server_type=data['server_type'],
        path=data['path'],
        size_mb=size_mb
    )
    
    # Increment Prometheus counter
    agent_reports_counter.labels(
        site=data['site'],
        sub_site=data['sub_site'],
        server_type=data['server_type']
    ).inc()
    
    return jsonify({'success': True, 'message': 'Data recorded'})


@app.route('/api/sites')
@login_required
def api_sites():
    """Get all sites configuration"""
    return jsonify(SITES_CONFIG)


@app.route('/api/summary')
@login_required
def api_summary():
    """Get summary of all sites with latest data and growth"""
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    summary = DiskUsage.get_all_sites_summary(user_env)
    
    # Enrich with growth data and log download URL
    for item in summary:
        item['growth_30d'] = DiskUsage.get_30day_growth(
            item['site'], item['sub_site'], item['server_type'], user_env
        )
        monthly = DiskUsage.get_monthly_growth(
            item['site'], item['sub_site'], item['server_type'], user_env
        )
        if monthly:
            avg_growth = sum(m['growth_mb'] for m in monthly) / len(monthly)
            item['monthly_avg_growth'] = round(avg_growth, 2)
        else:
            item['monthly_avg_growth'] = 0
    
    return jsonify(summary)


@app.route('/api/history/<site>/<sub_site>/<server_type>')
@login_required
def api_history(site, sub_site, server_type):
    """Get disk usage history for a specific server"""
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    days = request.args.get('days', 30, type=int)
    history = DiskUsage.get_history(site, sub_site, server_type, days, user_env)
    return jsonify(history)


@app.route('/api/monthly/<site>/<sub_site>/<server_type>')
@login_required
def api_monthly(site, sub_site, server_type):
    """Get monthly growth statistics"""
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    data = DiskUsage.get_monthly_growth(site, sub_site, server_type, user_env)
    return jsonify(data)


@app.route('/api/month-production/<site>/<sub_site>/<server_type>')
@login_required
def api_month_production(site, sub_site, server_type):
    """Get current and previous month production"""
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    data = DiskUsage.get_current_and_previous_month_growth(site, sub_site, server_type, user_env)
    return jsonify(data)


# ==================== Demo Data Route (for testing) ====================

@app.route('/api/demo/seed')
@login_required
def api_demo_seed():
    """Seed demo data for testing (disabled in production)"""
    # Only allow test environment users to seed data
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    if user_env != 'test':
        return jsonify({
            'success': False, 
            'error': '僅測試帳號可使用此功能',
            'message': 'Demo data seeding is only available for test accounts'
        }), 403
    
    import random
    from datetime import datetime, timedelta
    
    # First, clear existing demo data
    from models import get_db_connection
    conn = get_db_connection(user_env)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM disk_usage')
    conn.commit()
    conn.close()
    
    sites = [
        ('Site_A', 'SubSite_1', 'log_server'),
        ('Site_A', 'SubSite_1', 'backup_server'),
        ('Site_A', 'SubSite_2', 'log_server'),
        ('Site_A', 'SubSite_2', 'backup_server'),
        ('Site_A', 'SubSite_4', 'log_server'),
        ('Site_A', 'SubSite_4', 'backup_server'),
        ('Site_A', 'SubSite_6', 'log_server'),
        ('Site_A', 'SubSite_6', 'backup_server'),
        ('Site_B', 'SubSite_3', 'log_server'),
        ('Site_B', 'SubSite_3', 'backup_log_server'),
        ('Site_B', 'SubSite_5', 'log_server'),
        ('Site_B', 'SubSite_5', 'backup_log_server'),
        ('Site_B', 'SubSite_6', 'log_server'),
        ('Site_B', 'SubSite_6', 'backup_log_server'),
        ('Site_B', 'SubSite_Lab', 'log_server'),
        ('Site_B', 'SubSite_Lab', 'backup_log_server'),
        ('Site_B', 'SubSite_4', 'log_server'),
        ('Site_B', 'SubSite_4', 'backup_log_server'),
    ]
    
    now = datetime.now()
    
    # Generate 60 days of data with proper timestamps
    for site, sub_site, server_type in sites:
        base_size = random.randint(500, 2000)  # Starting size in MB
        for day in range(60, -1, -1):
            # Add some random growth each day (0-50 MB)
            base_size += random.randint(0, 50)
            record_time = now - timedelta(days=day)
            
            # Insert with specific timestamp
            conn = get_db_connection(user_env)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO disk_usage (site, sub_site, server_type, path, size_mb, recorded_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (site, sub_site, server_type, '/data', base_size, record_time.isoformat()))
            conn.commit()
            conn.close()
    
    return jsonify({'success': True, 'message': 'Demo data seeded'})


# ==================== Initialize ====================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=PORT)
