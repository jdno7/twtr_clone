"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User

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

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()

        self.client = app.test_client()

        self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)

        db.session.commit()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_add_message(self):
        """Can user add a message?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_add_message_unathorized(self):
        """Can user add a message?"""

        with self.client as c:

            resp = c.get("/messages/new", follow_redirects=True)
            html = resp.get_data(as_text=True)

            # Make sure it redirects
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized.', html)
            
    def setup_messages(self):
         
        m1 = Message(text='Test message one',user_id=self.testuser.id)
        m1.id = 1
        m2 = Message(text='Test message two', user_id=self.testuser.id)
        m2.id = 2
        m3 = Message(text='Test message three', user_id=self.testuser.id)
        m3.id = 3
        db.session.add_all([m1,m2,m3])
        db.session.commit()

        self.testuser.messages.append(m1)
        self.testuser.messages.append(m2)
        self.testuser.messages.append(m3)
        db.session.commit()
        # print(self.testuser.messages)

    def test_msg_show(self):
        self.setup_messages()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.get('/messages/1')
            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn('Test message one', html)

    def test_msg_delete(self):
        self.setup_messages()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id
            
            resp = c.post('/messages/1/delete', follow_redirects=True)
            html = resp.get_data(as_text=True)
            msgs = Message.query.all()
            
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(len(msgs), 2)
