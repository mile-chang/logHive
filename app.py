# LogHive - Main Flask Application
from datetime import datetime
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

# Track last data update time for smart polling
last_report_time = datetime.now().isoformat()


@login_manager.user_loader
def load_user(user_id):
    """Restore User object from session cookie on each request."""
    user_env = session.get('user_environment', 'production')
    return User.get_by_id(user_id, preferred_env=user_env)


# ==================== Web Routes ====================

@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')


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
    
    # Update last report time for smart polling
    global last_report_time
    last_report_time = datetime.now().isoformat()
    
    return jsonify({'success': True, 'message': 'Data recorded'})


@app.route('/api/last-update')
def api_last_update():
    """Get last data update timestamp for smart polling"""
    return jsonify({'last_update': last_report_time})


@app.route('/api/summary')
@login_required
def api_summary():
    """Get summary of all sites with latest data (card-level only)"""
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    summary = DiskUsage.get_all_sites_summary(user_env)
    
    # Enrich with growth metrics for cards and overview stats
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


@app.route('/api/detail/<site>/<sub_site>/<server_type>')
@login_required
def api_detail(site, sub_site, server_type):
    """Get detailed data for Modal: history chart + month production stats"""
    user_env = current_user.environment if current_user.is_authenticated else 'production'
    days = request.args.get('days', 30, type=int)
    history = DiskUsage.get_history(site, sub_site, server_type, days, user_env)
    month_data = DiskUsage.get_current_and_previous_month_growth(
        site, sub_site, server_type, user_env
    )
    return jsonify({
        'history': history,
        'current_month_growth': month_data['current_month_growth'],
        'previous_month_growth': month_data['previous_month_growth']
    })


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
    
    # Define servers with varying data density for Dynamic Rendering testing
    # Most servers have 60 days (dense), some have fewer days (sparse) to show data points
    sites = [
        ('Site_A', 'SubSite_1', 'log_server', 60),
        ('Site_A', 'SubSite_1', 'backup_server', 60),
        ('Site_A', 'SubSite_2', 'log_server', 60),
        ('Site_A', 'SubSite_2', 'backup_server', 10),     # Sparse: 10 days
        ('Site_A', 'SubSite_4', 'log_server', 60),
        ('Site_A', 'SubSite_4', 'backup_server', 7),      # Sparse: 7 days
        ('Site_A', 'SubSite_6', 'log_server', 60),
        ('Site_A', 'SubSite_6', 'backup_server', 60),
        ('Site_B', 'SubSite_3', 'log_server', 60),
        ('Site_B', 'SubSite_3', 'backup_log_server', 15), # Sparse: 15 days
        ('Site_B', 'SubSite_5', 'log_server', 60),
        ('Site_B', 'SubSite_5', 'backup_log_server', 60),
        ('Site_B', 'SubSite_6', 'log_server', 60),
        ('Site_B', 'SubSite_6', 'backup_log_server', 60),
        ('Site_B', 'SubSite_Lab', 'log_server', 5),       # Sparse: 5 days
        ('Site_B', 'SubSite_Lab', 'backup_log_server', 60),
        ('Site_B', 'SubSite_4', 'log_server', 60),
        ('Site_B', 'SubSite_4', 'backup_log_server', 20), # Sparse: 20 days
    ]
    
    now = datetime.now()
    
    # Generate data with per-server day counts for Dynamic Rendering testing
    for site, sub_site, server_type, num_days in sites:
        base_size = random.randint(500, 2000)  # Starting size in MB
        for day in range(num_days, -1, -1):
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
    
    # Update last report time so the auto-update indicator shows "剛剛更新"
    global last_report_time
    last_report_time = datetime.now().isoformat()
    
    return jsonify({'success': True, 'message': 'Demo data seeded'})



# ==================== Initialize ====================

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=PORT)
