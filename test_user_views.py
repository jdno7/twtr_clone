"""User Views tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from sqlite3 import IntegrityError
from unittest import TestCase
from sqlalchemy import exc
import psycopg2
from psycopg2.errors import  UniqueViolation

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False


class UserMessageTestCase(TestCase):
    """Test Message Model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(
                                    "testuser",
                                    "testing@test.com",
                                    "sadkfjasd",
                                    None)
        self.testuser.id = 9

        self.u1 = User.signup("testuser1", "test1@test.com", "asdfasdf", None)
        self.u1.id = 99
        self.u2 = User.signup("testuser2", "test2@test.com", "sdfadsfadfdf", None)
        self.u2.id = 999
        self.u3 = User.signup("testuser3", "test3@test.com", "qerqwerqew", None)
        self.u3.id = 9999
        self.u4 = User.signup("testuser4", "test4@test.com", "zxcvxvzxcvc", None)
        self.u4 = 99999

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_users_index(self):
        with self.client as c :
            resp = c.get('/users')

            self.assertIn("testuser", str(resp.data))
            self.assertIn("testuser1", str(resp.data))
            self.assertIn("testuser2", str(resp.data))
            self.assertIn("testuser3", str(resp.data))
            self.assertIn("testuser4", str(resp.data))
            
    def test_login_page(self):
        with self.client as c:
            resp = c.get('/login')
            html = resp.get_data(as_text=True)
        # print(html)
        self.assertIn('<h2 class="join-message">Welcome back.</h2>', html)
        self.assertEqual(resp.status_code, 200)

    def test_login(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/login", data={"username":"testuser", "password":"sadkfjasd"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
           
            self.assertEqual(resp.status_code, 200)
            self.assertIn('<div class="alert alert-success">Hello, testuser!</div>', html)

    def test_invalid_password(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/login", data={"username":"testuser", "password":"invalid"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
           
            self.assertEqual(resp.status_code, 200)
            self.assertIn(' <div class="alert alert-danger">Invalid credentials.</div>', html)

    def test_invalid_username(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/login", data={"username":"invalid", "password":"sadkfjasd"}, follow_redirects=True)
            html = resp.get_data(as_text=True)
           
            self.assertEqual(resp.status_code, 200)
            self.assertIn(' <div class="alert alert-danger">Invalid credentials.</div>', html)

    def test_logout(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

        resp = c.get('/logout', follow_redirects=True) 
        html = resp.get_data(as_text=True)

        self.assertEqual(resp.status_code, 200)
        self.assertIn('Logged Out!', html)
   
    def setup_followers(self):

        u1 = User.query.get(99)
        u2 = User.query.get(999)
        u3 = User.query.get(9999)

        self.testuser.following.append(u1)
        self.testuser.following.append(u2)
        self.testuser.following.append(u3)
        u1.following.append(self.testuser)
        u2.following.append(self.testuser)
        u3.following.append(self.testuser)

        db.session.commit()
    


    def test_home(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get('/')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>@testuser</p>', html)
            self.assertIn('<a href="/users/9/following">3</a>', html)
            self.assertIn('<a href="/users/9/followers">3</a>', html)
    def setup_messages(self):
        m1 = Message(text='Test message one')
        m2 = Message(text='Test message two')
        m3 = Message(text='Test message three')

        self.testuser.messages.append(m1)
        self.testuser.messages.append(m2)
        self.testuser.messages.append(m3)
        db.session.commit()

    def test_user_show(self):
        self.setup_messages()
        with self.client as c:

            resp = c.get(f'/users/{self.testuser.id}')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('<p>Test message three</p>', html)

    def test_edit_profile_view_unauthorized(self):
        with self.client as c:
            resp = c.get(f'/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", html)

    def test_edit_profile_view(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get(f'/users/profile', follow_redirects=True)
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Edit this user!', html)
            self.assertIn('<input class="form-control" id="username" name="username" placeholder="Username" required type="text" value="testuser">', html)
                 
    def setup_likes(self):
        self.setup_messages()
        m1 = Message.query.get(1)
        m2 = Message.query.get(2)
        
        u1 = self.u1
        
        u1.likes.append(m1)
        u1.likes.append(m2)
        db.session.commit()
       

    def test_likes(self):
        self.setup_likes()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id

            resp = c.get(f'/users/{self.u1.id}') 
            html = resp.get_data(as_text=True)
            self.assertIn('<a href="/users/likes">2</a>', html) 
             

    def test_remove_likes(self):
        """cant figure out lazy load error"""
        self.setup_likes()
        m = Message.query.get(1)
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.u1.id
            
            resp = c.post(f'/users/delete_like/{m.id}', follow_redirects=True) 
            likes = Likes.query.all()
            html = resp.get_data(as_text=True)
            self.assertEqual(len(likes), 1)   


            

            
           
    