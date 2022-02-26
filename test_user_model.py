"""User model tests."""

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


class UserModelTestCase(TestCase):
    """Test User Model."""

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

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_user_model(self):
        """following / follower tests"""

        u = User(
        email="test@test.com",
        username="testuser",
        password="HASHED_PASSWORD"
        )
        following = User(
            email="test2@test.com",
            username="following",
            password="HASHED_PASSWORD2"
        )

        db.session.add_all([u,following])
        db.session.commit()

        u.following.append(following)
        db.session.commit()

        self.assertEqual(u.is_following(following), True)
        self.assertEqual(following.is_following(u), False)
        self.assertEqual(following.is_followed_by(u), True)
        self.assertEqual(u.is_followed_by(following), False)

    def test_user_signup(self):
        """Testing User Sign-up and Validation"""

        u = User.signup(
            "testuser",
            "test@test.com",
            "HASHED_PASSWORD",
            "https://google.com"
            )
        id = 9
        u.id = id
        
        db.session.commit()
        self.assertEqual(len(User.query.all()), 1)

    def test_same_username(self):
        u = User.signup(
            "testuser",
            "test@test.com",
            "HASHED_PASSWORD",
            "https://google.com"
            )
        id = 9
        u.id = id
        db.session.commit()

        u2 = User.signup(
            "testuser",
            'test2@test.com',
            'HASHED_PWD2',
            "https://google.com"
        )
        u2id = 99
        u2.id = u2id
     

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        self.assertTrue('UniqueViolation' in str(context.exception))
        
    def test_null_email(self):
        u = User.signup('testuser', None, 'asdkfah', None)
        uid = 9
        u.id = uid

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        self.assertTrue('NotNullViolation' in str(context.exception))

    def test_null_pwd(self):
        u = User.signup('testuser', 'test@test.com', None, None)
        uid = 9
        u.id = uid

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        self.assertTrue('NotNullViolation' in str(context.exception))

    def test_null_pwd(self):
        u = User.signup(None, 'test@test.com', 'asdkfah', None)
        uid = 9
        u.id = uid

        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()
        self.assertTrue('NotNullViolation' in str(context.exception))
      
    def test_login(self):

        u = User.signup(
            "testuser",
            'test2@test.com',
            'HASHED_PWD2',
            "https://google.com"
        )
        u2id = 99
        u.id = u2id
        db.session.commit()

        self.assertEqual(User.authenticate('testuser', 'HASHED_PWD2'), u)
        self.assertEqual(User.authenticate('invalid_usernmae', 'HASHED_PWD2'), False)
        self.assertEqual(User.authenticate('testuser', 'wrong_pwd'), False)


