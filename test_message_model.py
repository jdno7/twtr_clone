"""Message model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from sqlite3 import IntegrityError
from unittest import TestCase
from sqlalchemy import exc
import psycopg2
from psycopg2.errors import  UniqueViolation

from models import db, User, Message, Follows

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()


class UserMessageTestCase(TestCase):
    """Test Message Model."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()

        self.client = app.test_client()

    def tearDown(self):
        res = super().tearDown()
        db.session.rollback()
        return res

    def test_message(self):
        """Create a message"""
        
        u = User.signup("testing", "test@test.com", "password", None)
        u.id = 9
        db.session.add(u)
        db.session.commit()

        
        m = Message(
            text='Testing a Warble',
            user_id = 9
            )
        m.id = 7
        db.session.add(m)
        db.session.commit()

        self.assertEqual(len(Message.query.all()), 1)
        self.assertEqual(m.text, "Testing a Warble")

    def test_likes(self):
        """Like a message"""
        u = User.signup("testing", "test@test.com", "password", None)
        u.id = 9
        db.session.add(u)
        db.session.commit()

        m = Message(
            text='Testing a Warble',
            user_id = 9
            )
        m.id = 7
        db.session.add(m)
        db.session.commit()

        u.likes.append(m)
        db.session.commit()

        self.assertEqual(u.likes[0].text, "Testing a Warble")
        
        