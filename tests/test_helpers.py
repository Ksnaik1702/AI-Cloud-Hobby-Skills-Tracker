import json
import threading
import time
import unittest
import uuid
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from http.server import ThreadingHTTPServer

from backend import server
from backend.server import progress_percent, pw_hash, pw_ok, token, token_user




class LocalApiFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_db = server.DB
        cls.db_path = Path(__file__).parent / ('test-' + uuid.uuid4().hex + '.db')
        server.DB = cls.db_path
        server.init()
        cls.httpd = ThreadingHTTPServer(('127.0.0.1', 0), server.Handler)
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = 'http://127.0.0.1:' + str(cls.httpd.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.thread.join(timeout=3)
        server.DB = cls.old_db
        for _ in range(20):
            try:
                cls.db_path.unlink(missing_ok=True)
                break
            except PermissionError:
                time.sleep(0.1)

    def call_api(self, path, method='GET', body=None, bearer=None):
        headers = {}
        raw = None
        if body is not None:
            headers['Content-Type'] = 'application/json'
            raw = json.dumps(body).encode('utf-8')
        if bearer:
            headers['Authorization'] = 'Bearer ' + bearer
        request = Request(self.base + path, data=raw, headers=headers, method=method)
        with urlopen(request, timeout=5) as response:
            return json.loads(response.read().decode('utf-8'))

    def test_skill_goal_practice_analytics_and_community_flow(self):
        suffix = uuid.uuid4().hex[:10]
        account = self.call_api('/api/auth/register', 'POST', {
            'name': 'Test User', 'username': 'test_' + suffix,
            'email': suffix + '@example.test', 'password': 'test-password-123'
        })
        bearer = account['token']
        skill = self.call_api('/api/skills', 'POST', {
            'name': 'Guitar', 'category': 'Music', 'level': 'BEGINNER'
        }, bearer)
        updated_skill = self.call_api('/api/skills/' + skill['id'], 'PUT', {
            'name': 'Acoustic Guitar', 'category': 'Music', 'level': 'INTERMEDIATE',
            'target_level': 'ADVANCED', 'description': 'Chord transitions', 'status': 'ACTIVE'
        }, bearer)
        self.assertEqual(updated_skill['name'], 'Acoustic Guitar')
        self.assertEqual(updated_skill['level'], 'INTERMEDIATE')
        goal = self.call_api('/api/goals', 'POST', {
            'skill_id': skill['id'], 'title': 'Practice one hour', 'target': 1, 'unit': 'hours', 'milestones': [20, 60, 100]
        }, bearer)
        saved_goal = next(item for item in self.call_api('/api/goals', bearer=bearer) if item['id'] == goal['id'])
        self.assertEqual(saved_goal['milestones'], [20, 60, 100])
        self.call_api('/api/goals/' + goal['id'], 'PUT', {
            'skill_id': skill['id'], 'title': 'One hour of guitar', 'target': 1, 'unit': 'hours', 'milestones': [25, 75, 100]
        }, bearer)
        updated_goal = next(item for item in self.call_api('/api/goals', bearer=bearer) if item['id'] == goal['id'])
        self.assertEqual(updated_goal['title'], 'One hour of guitar')
        self.assertEqual(updated_goal['milestones'], [25, 75, 100])
        self.call_api('/api/practice', 'POST', {
            'skill_id': skill['id'], 'minutes': 60, 'activity': 'Chord practice'
        }, bearer)
        analytics = self.call_api('/api/analytics/dashboard', bearer=bearer)
        self.assertEqual(analytics['total_minutes'], 60)
        self.assertEqual(analytics['month_minutes'], 60)
        self.assertEqual(len(analytics['month_series']), 6)
        self.assertEqual(analytics['longest_streak'], 1)
        self.assertEqual(analytics['goals_completed'], 1)
        saved_goal = self.call_api('/api/goals', bearer=bearer)[0]
        self.assertEqual(saved_goal['id'], goal['id'])
        self.assertEqual(saved_goal['progress'], 100)

        post = self.call_api('/api/posts', 'POST', {'content': 'First practice update!', 'skill_id': skill['id']}, bearer)
        self.call_api('/api/posts/' + post['id'] + '/like', 'POST', {}, bearer)
        self.call_api('/api/posts/' + post['id'] + '/comments', 'POST', {'text': 'Keep it up!'}, bearer)
        feed_post = next(item for item in self.call_api('/api/feed', bearer=bearer) if item['id'] == post['id'])
        self.assertEqual(feed_post['likes'], 1)
        self.assertEqual(feed_post['comments'], 1)
        self.assertEqual(feed_post['skill_name'], 'Acoustic Guitar')
        self.assertEqual(feed_post['skill_category'], 'Music')
        self.assertTrue(feed_post['liked'])
        request = Request(self.base + '/api/files/upload', method='POST', headers={'Authorization': 'Bearer ' + bearer})
        with self.assertRaises(HTTPError) as error:
            urlopen(request, timeout=5)
        self.assertEqual(error.exception.code, 404)
        error.exception.close()


class SecurityAndProgressTests(unittest.TestCase):

    def test_password_hash_matches_only_original_password(self):
        encoded = pw_hash('correct horse battery staple')
        self.assertTrue(pw_ok('correct horse battery staple', encoded))
        self.assertFalse(pw_ok('incorrect password', encoded))

    def test_password_hash_uses_a_different_salt_each_time(self):
        first = pw_hash('same password')
        second = pw_hash('same password')
        self.assertNotEqual(first, second)
        self.assertTrue(pw_ok('same password', first))
        self.assertTrue(pw_ok('same password', second))

    def test_session_token_round_trip(self):
        signed = token('user-123')
        self.assertEqual(token_user(signed), 'user-123')

    def test_modified_session_token_is_rejected(self):
        signed = token('user-123')
        self.assertIsNone(token_user(signed + 'tampered'))

    def test_goal_progress_is_bounded(self):
        self.assertEqual(progress_percent(18, 30), 60)
        self.assertEqual(progress_percent(40, 30), 100)
        self.assertEqual(progress_percent(-2, 30), 0)
        self.assertEqual(progress_percent(3, 0), 0)


if __name__ == '__main__':
    unittest.main()
