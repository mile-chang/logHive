"""
LogHive Unit Tests
Covers: _calc_positive_growth, DiskUsage model operations, Flask API endpoints
Uses in-memory SQLite - does NOT touch any real database.
"""

import unittest
import json
import sqlite3
import sys
import os
import unittest.mock as mock

os.environ['TESTING'] = '1'

# ── In-memory DB setup ──────────────────────────────────────────────────────

_real_conn = sqlite3.connect(':memory:', check_same_thread=False)
_real_conn.row_factory = sqlite3.Row
_real_conn.executescript('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        environment TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS disk_usage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        site TEXT NOT NULL,
        sub_site TEXT NOT NULL,
        server_type TEXT NOT NULL,
        path TEXT NOT NULL,
        size_mb REAL NOT NULL,
        recorded_at TIMESTAMP DEFAULT (datetime('now','localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_disk_usage_lookup
        ON disk_usage (site, sub_site, server_type, recorded_at);
''')
_real_conn.commit()


class _NoCloseConn:
    """Wrap a real connection so .close() is a no-op (keeps in-memory DB alive)."""
    def __init__(self, conn):
        self._conn = conn
        self.row_factory = conn.row_factory

    def cursor(self):
        return self._conn.cursor()

    def execute(self, *args, **kwargs):
        return self._conn.execute(*args, **kwargs)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        return self._conn.rollback()

    def close(self):
        pass  # intentionally no-op

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass


def _fake_get_db(environment='test'):
    return _NoCloseConn(_real_conn)


# ── Patch before importing models / app ─────────────────────────────────────

with mock.patch.dict('sys.modules', {}):
    # Patch at the source before any import
    import config  # import config first (no db calls)

with mock.patch('models.get_db_connection', side_effect=_fake_get_db), \
     mock.patch('models.get_database_path', return_value=':memory:'):
    import models as models_module
    from models import DiskUsage, User

# Override at module level so all subsequent calls use in-memory
models_module.get_db_connection = _fake_get_db


# ════════════════════════════════════════════════════════════════════════════
# 1. Pure logic: _calc_positive_growth
# ════════════════════════════════════════════════════════════════════════════

class TestCalcPositiveGrowth(unittest.TestCase):
    def g(self, data):
        return DiskUsage._calc_positive_growth(data)

    def test_pure_growth(self):
        self.assertEqual(self.g([50, 80, 120]), 70)

    def test_growth_with_deletion(self):
        # 85→120(+35), skip 120→60, 60→85(+25) = 60
        self.assertEqual(self.g([85, 120, 60, 85]), 60)

    def test_only_deletions(self):
        self.assertEqual(self.g([100, 50, 30]), 0)

    def test_delete_then_grow_back(self):
        # skip 100→10, 10→100(+90)
        self.assertEqual(self.g([100, 10, 100]), 90)

    def test_flat(self):
        self.assertEqual(self.g([100, 100, 100]), 0)

    def test_single_point(self):
        self.assertEqual(self.g([100]), 0)

    def test_empty(self):
        self.assertEqual(self.g([]), 0)

    def test_multiple_cycles(self):
        # +50, skip, +50, skip, +40 = 140
        self.assertEqual(self.g([50, 100, 30, 80, 20, 60]), 140)

    def test_float_precision(self):
        self.assertEqual(self.g([1.5, 3.7, 2.1, 5.3]), 5.4)

    def test_returns_float(self):
        result = self.g([1.0, 2.5])
        self.assertIsInstance(result, float)
        self.assertEqual(result, 1.5)


# ════════════════════════════════════════════════════════════════════════════
# 2. DiskUsage - record & history
# ════════════════════════════════════════════════════════════════════════════

def _insert(site, sub, stype, size_mb, timestamp=None):
    if timestamp:
        _real_conn.execute(
            'INSERT INTO disk_usage (site, sub_site, server_type, path, size_mb, recorded_at)'
            ' VALUES (?, ?, ?, ?, ?, ?)',
            (site, sub, stype, '/data', size_mb, timestamp)
        )
    else:
        _real_conn.execute(
            'INSERT INTO disk_usage (site, sub_site, server_type, path, size_mb)'
            ' VALUES (?, ?, ?, ?, ?)',
            (site, sub, stype, '/data', size_mb)
        )
    _real_conn.commit()


class TestDiskUsageRecord(unittest.TestCase):
    SITE  = 'TestSite'
    SUB   = 'Sub1'
    STYPE = 'log_server'

    def setUp(self):
        _real_conn.execute('DELETE FROM disk_usage WHERE site = ?', (self.SITE,))
        _real_conn.commit()

    def test_history_returns_inserted_records(self):
        _insert(self.SITE, self.SUB, self.STYPE, 100.0)
        _insert(self.SITE, self.SUB, self.STYPE, 200.0)
        history = DiskUsage.get_history(self.SITE, self.SUB, self.STYPE, days=30)
        self.assertEqual(len(history), 2)

    def test_history_record_has_expected_keys(self):
        _insert(self.SITE, self.SUB, self.STYPE, 50.0)
        history = DiskUsage.get_history(self.SITE, self.SUB, self.STYPE, days=30)
        self.assertIn('size_mb', history[0])
        self.assertIn('recorded_at', history[0])

    def test_empty_history_for_unknown_site(self):
        history = DiskUsage.get_history('NoSite', 'NoSub', 'notype', days=30)
        self.assertEqual(history, [])


# ════════════════════════════════════════════════════════════════════════════
# 3. DiskUsage - monthly growth
# ════════════════════════════════════════════════════════════════════════════

class TestMonthlyGrowth(unittest.TestCase):
    SITE  = 'GrowthSite'
    SUB   = 'Sub1'
    STYPE = 'log_server'

    def setUp(self):
        _real_conn.execute('DELETE FROM disk_usage WHERE site = ?', (self.SITE,))
        _real_conn.commit()

    def _seq(self, sizes, month='2026-01'):
        for i, sz in enumerate(sizes):
            ts = f'{month}-15 {i:02d}:00:00'
            _insert(self.SITE, self.SUB, self.STYPE, sz, ts)

    def test_positive_growth(self):
        self._seq([50, 80, 120], '2026-01')   # +30 +40 = 70
        result = DiskUsage.get_monthly_growth(self.SITE, self.SUB, self.STYPE)
        month_data = next(r for r in result if r['month'] == '2026-01')
        self.assertAlmostEqual(month_data['growth_mb'], 70.0)

    def test_growth_ignores_deletion(self):
        # 100→200(+100), 200→50(skip), 50→100(+50) = 150
        self._seq([100, 200, 50, 100], '2026-01')
        result = DiskUsage.get_monthly_growth(self.SITE, self.SUB, self.STYPE)
        month_data = next(r for r in result if r['month'] == '2026-01')
        self.assertAlmostEqual(month_data['growth_mb'], 150.0)

    def test_only_decrease_growth_is_zero(self):
        self._seq([200, 100, 50], '2026-01')
        result = DiskUsage.get_monthly_growth(self.SITE, self.SUB, self.STYPE)
        month_data = next(r for r in result if r['month'] == '2026-01')
        self.assertEqual(month_data['growth_mb'], 0)

    def test_current_and_previous_month(self):
        from datetime import datetime
        now = datetime.now()
        cur  = now.strftime('%Y-%m')
        prev = f'{now.year}-{now.month - 1:02d}' if now.month > 1 else f'{now.year - 1}-12'

        self._seq([10, 50, 90], cur)   # +40 +40 = 80
        self._seq([20, 60],     prev)  # +40

        r = DiskUsage.get_current_and_previous_month_growth(self.SITE, self.SUB, self.STYPE)
        self.assertAlmostEqual(r['current_month_growth'], 80.0)
        self.assertAlmostEqual(r['previous_month_growth'], 40.0)

    def test_no_data_returns_zero(self):
        r = DiskUsage.get_current_and_previous_month_growth('NoSite', 'NoSub', 'notype')
        self.assertEqual(r['current_month_growth'], 0)
        self.assertEqual(r['previous_month_growth'], 0)

    def test_30day_growth_matches_current_month_growth(self):
        """Verify get_30day_growth == current_month_growth (same algorithm)."""
        from datetime import datetime
        cur = datetime.now().strftime('%Y-%m')
        # Simulate: growth with cleanup in the middle: 10→50(+40), 50→20(skip), 20→60(+40) = 80
        self._seq([10, 50, 20, 60], cur)

        g30 = DiskUsage.get_30day_growth(self.SITE, self.SUB, self.STYPE)
        r = DiskUsage.get_current_and_previous_month_growth(self.SITE, self.SUB, self.STYPE)
        self.assertAlmostEqual(g30, 80.0)
        self.assertAlmostEqual(g30, r['current_month_growth'])


# ════════════════════════════════════════════════════════════════════════════
# 4. Flask API (test client, no login required endpoints)
# ════════════════════════════════════════════════════════════════════════════

class TestFlaskAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with mock.patch('models.get_db_connection', side_effect=_fake_get_db):
            import app as flask_app
        flask_app.app.config['TESTING'] = True
        flask_app.app.config['WTF_CSRF_ENABLED'] = False
        cls.client = flask_app.app.test_client()

    def test_login_page_loads(self):
        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)

    def test_api_report_wrong_token_returns_401(self):
        res = self.client.post('/api/report',
            data=json.dumps({
                'token': 'wrong-token', 'site': 'A',
                'sub_site': 'S1', 'server_type': 'log',
                'path': '/data', 'size_mb': 100
            }),
            content_type='application/json')
        self.assertEqual(res.status_code, 401)

    def test_api_summary_redirects_without_login(self):
        res = self.client.get('/api/summary')
        self.assertIn(res.status_code, [302, 401])

    def test_login_wrong_credentials_stays_on_login(self):
        res = self.client.post('/login',
            data={'username': 'admin', 'password': 'utterly_wrong'},
            follow_redirects=True)
        self.assertEqual(res.status_code, 200)


if __name__ == '__main__':
    runner = unittest.TextTestRunner(verbosity=2)
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
