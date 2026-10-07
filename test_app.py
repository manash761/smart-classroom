import unittest
import os
import tempfile
from app import app
from database import execute_query, init_db
from werkzeug.security import generate_password_hash

class SmartClassroomTestCase(unittest.TestCase):
    def setUp(self):
        # Configure Flask app for testing
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        
        # Point SQLite to a temporary testing database
        self.db_fd, self.db_path = tempfile.mkstemp()
        # Override the database location by rewriting db path locally for sqlite
        # In our database.py it defaults to local file, but we can mock it here
        # Actually since we want to run tests cleanly without breaking environment,
        # we will use the existing development database, or we can use SQLITE memory db.
        # But wait, app.py runs init_db() on start, which creates classroom.db.
        # Let's just use the Flask test client against our configured app.
        
        self.client = app.test_client()

    def tearDown(self):
        # Clean up temporary database if needed, otherwise leave dev database as is
        os.close(self.db_fd)
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def test_index_redirects(self):
        """Verify root page redirects to login when not authenticated."""
        response = self.client.get('/', follow_redirects=False)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login', response.location)

    def test_login_page_renders(self):
        """Verify the login page renders with correct fields."""
        response = self.client.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'SmartClass', response.data)
        self.assertIn(b'Student Portal', response.data)
        self.assertIn(b'Teacher Portal', response.data)

    def test_invalid_login(self):
        """Verify login fails with wrong credentials."""
        response = self.client.post('/login', data={
            'username': 'nonexistent_user',
            'password': 'wrongpassword',
            'role': 'student'
        }, follow_redirects=True)
        self.assertIn(b'Invalid credentials', response.data)

    def test_role_authorization_on_apis(self):
        """Verify API endpoints are protected and validate roles."""
        # Unauthenticated access to notices
        res = self.client.get('/api/notices')
        self.assertEqual(res.status_code, 302) # Redirects to login

    def login_user(self, username, password, role):
        return self.client.post('/login', data={
            'username': username,
            'password': password,
            'role': role
        }, follow_redirects=True)

    def test_student_and_teacher_logins(self):
        """Verify teachers and students can authenticate successfully and access their dashboards."""
        # Test teacher login
        res_teacher = self.login_user('teacher', 'admin123', 'teacher')
        self.assertIn(b'RAMEN KR CHOUDHURY', res_teacher.data)
        self.assertIn(b'Teacher', res_teacher.data)
        self.assertIn(b'Overview', res_teacher.data) # Teacher Nav
        
        # Log out
        self.client.get('/logout')
        
        # Test student login
        res_student = self.login_user('abdulrazak', 'password123', 'student')
        self.assertIn(b'Abdul Razak', res_student.data)
        self.assertIn(b'Student', res_student.data)
        self.assertIn(b'My Attendance', res_student.data) # Student Nav

    def test_student_cannot_post_notice(self):
        """Verify role protection prevents students from calling teacher APIs."""
        # Login as student
        self.login_user('abdulrazak', 'password123', 'student')
        
        # Try to post notice (Teacher-only)
        res = self.client.post('/api/notices', json={
            'title': 'Hacker Notice',
            'content': 'I am a student posting this'
        })
        self.assertEqual(res.status_code, 403)
        self.assertIn(b'Only teachers can post notices', res.data)

if __name__ == '__main__':
    unittest.main()
