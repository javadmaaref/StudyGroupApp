# app/models.py
from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager


@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id))


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    groups_owned = db.relationship('StudyGroup', backref='admin', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class StudyGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text)
    subject = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    members = db.relationship('GroupMembership', backref='group', lazy='dynamic')
    sessions = db.relationship('StudySession', backref='group', lazy='dynamic')
    messages = db.relationship('GroupMessage', backref='study_group', lazy='dynamic')


class GroupMembership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref='group_memberships')


class StudySession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'))
    date = db.Column(db.DateTime, nullable=False)
    location = db.Column(db.String(128))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    rsvps = db.relationship('SessionRSVP', backref='study_session', lazy='dynamic')  # Changed backref name

    def get_user_rsvp(self, user):
        return SessionRSVP.query.filter_by(
            session_id=self.id,
            user_id=user.id
        ).first()

    def get_rsvp_counts(self):
        counts = {
            'going': SessionRSVP.query.filter_by(session_id=self.id, status='going').count(),
            'not_going': SessionRSVP.query.filter_by(session_id=self.id, status='not_going').count(),
            'maybe': SessionRSVP.query.filter_by(session_id=self.id, status='maybe').count()
        }
        return counts


class SessionRSVP(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('study_session.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(20))  # 'going', 'not_going', 'maybe'
    comment = db.Column(db.String(200))  # Optional comment
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='session_rsvps')
    # Remove the session relationship since it's defined in StudySession class


class GroupMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    group_id = db.Column(db.Integer, db.ForeignKey('study_group.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='messages')