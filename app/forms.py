# app/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, DateTimeField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class GroupForm(FlaskForm):
    name = StringField('Group Name', validators=[DataRequired()])
    subject = StringField('Subject', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Group')

class SessionForm(FlaskForm):
    date = DateTimeField(
        'Date and Time',
        format='%Y-%m-%dT%H:%M',  # HTML5 datetime-local format
        validators=[DataRequired()],
        render_kw={"type": "datetime-local"}
    )
    location = StringField('Location', validators=[DataRequired()])
    description = TextAreaField('Description')
    submit = SubmitField('Schedule Session')


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    current_password = PasswordField('Current Password')
    new_password = PasswordField('New Password', validators=[
        Optional(),
        Length(min=6)
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Update Profile')
