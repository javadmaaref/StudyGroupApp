from datetime import datetime, timezone
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, StudyGroup, StudySession, GroupMembership, GroupMessage, SessionRSVP
from app.forms import LoginForm, RegistrationForm, GroupForm, SessionForm, ProfileForm

# Create blueprints
auth_bp = Blueprint('auth', __name__)
groups_bp = Blueprint('groups', __name__, url_prefix='/groups')
sessions_bp = Blueprint('sessions', __name__, url_prefix='/sessions')


# Utility functions
def check_group_membership(user_id, group_id):
    """Check if a user is a member of a group"""
    return GroupMembership.query.filter_by(
        user_id=user_id,
        group_id=group_id
    ).first() is not None


def check_group_admin(user_id, group_id):
    """Check if a user is the admin of a group"""
    group = StudyGroup.query.get_or_404(group_id)
    return user_id == group.admin_id


def format_timestamp(timestamp):
    """Format timestamp consistently across the application"""
    return timestamp.strftime('%Y-%m-%d %H:%M')


# Base route
@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('groups.list'))
    return render_template('home.html')


# Authentication routes
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('groups.list'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(url_for('groups.list'))
        flash('Invalid username or password')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('groups.list'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful!')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        if form.new_password.data:
            if not current_user.check_password(form.current_password.data):
                flash('Current password is incorrect')
                return redirect(url_for('auth.profile'))
            current_user.set_password(form.new_password.data)

        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your profile has been updated.')
        return redirect(url_for('auth.profile'))

    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email

    context = {
        'form': form,
        'my_groups': StudyGroup.query.filter_by(admin_id=current_user.id).all(),
        'member_of': StudyGroup.query.join(GroupMembership).filter(
            GroupMembership.user_id == current_user.id
        ).all(),
        'recent_messages': GroupMessage.query.filter_by(user_id=current_user.id)
        .order_by(GroupMessage.timestamp.desc())
        .limit(5)
        .all()
    }

    return render_template('auth/profile.html', **context)


# Group routes
@groups_bp.route('/')
@login_required
def list():
    groups = StudyGroup.query.all()
    return render_template('groups/list.html', groups=groups)


@groups_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = GroupForm()
    if form.validate_on_submit():
        group = StudyGroup(
            name=form.name.data,
            subject=form.subject.data,
            description=form.description.data,
            admin_id=current_user.id
        )
        db.session.add(group)
        membership = GroupMembership(user_id=current_user.id, group=group)
        db.session.add(membership)
        db.session.commit()
        flash('Study group created successfully!')
        return redirect(url_for('groups.list'))
    return render_template('groups/create.html', form=form)


@groups_bp.route('/<int:id>')
@login_required
def details(id):
    group = StudyGroup.query.get_or_404(id)
    sessions = group.sessions.order_by(StudySession.date).all()
    return render_template('groups/details.html', group=group, sessions=sessions)


@groups_bp.route('/<int:id>/join', methods=['POST'])
@login_required
def join(id):
    if check_group_membership(current_user.id, id):
        flash('You are already a member of this group.')
        return redirect(url_for('groups.details', id=id))

    membership = GroupMembership(user_id=current_user.id, group_id=id)
    db.session.add(membership)
    db.session.commit()
    flash('Successfully joined the group!')
    return redirect(url_for('groups.details', id=id))


@groups_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_group(id):
    if not check_group_admin(current_user.id, id):
        flash('Only group admin can delete the group.')
        return redirect(url_for('groups.details', id=id))

    StudySession.query.filter_by(group_id=id).delete()
    GroupMembership.query.filter_by(group_id=id).delete()
    StudyGroup.query.filter_by(id=id).delete()
    db.session.commit()

    flash('Group has been deleted.')
    return redirect(url_for('groups.list'))


@groups_bp.route('/<int:group_id>/remove_member/<int:user_id>', methods=['POST'])
@login_required
def remove_member(group_id, user_id):
    if not check_group_admin(current_user.id, group_id):
        flash('Only group admin can remove members.')
        return redirect(url_for('groups.details', id=group_id))

    if user_id == current_user.id:
        flash('Cannot remove group admin.')
        return redirect(url_for('groups.details', id=group_id))

    membership = GroupMembership.query.filter_by(
        group_id=group_id,
        user_id=user_id
    ).first_or_404()

    db.session.delete(membership)
    db.session.commit()
    flash('Member has been removed from the group.')
    return redirect(url_for('groups.details', id=group_id))


# Chat routes
@groups_bp.route('/<int:id>/chat', methods=['GET', 'POST'])
@login_required
def chat(id):
    if not check_group_membership(current_user.id, id):
        flash('You must be a member of the group to access the chat.')
        return redirect(url_for('groups.details', id=id))

    group = StudyGroup.query.get_or_404(id)

    if request.method == 'POST':
        content = request.form.get('message', '').strip()
        if content:
            message = GroupMessage(
                content=content,
                group_id=id,
                user_id=current_user.id,
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(message)
            db.session.commit()

            return jsonify({
                'status': 'success',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'username': current_user.username,
                    'timestamp': format_timestamp(message.timestamp),
                    'is_own': True
                }
            })

    messages = GroupMessage.query.filter_by(group_id=id) \
        .order_by(GroupMessage.timestamp.desc()) \
        .limit(50) \
        .all()

    return render_template('groups/chat.html', group=group, messages=messages)


@groups_bp.route('/<int:id>/get_messages')
@login_required
def get_messages(id):
    if not check_group_membership(current_user.id, id):
        return jsonify({'error': 'Access denied'}), 403

    messages = GroupMessage.query \
        .filter_by(group_id=id) \
        .order_by(GroupMessage.timestamp.desc()) \
        .limit(50) \
        .all()

    return jsonify([{
        'id': msg.id,
        'content': msg.content,
        'username': msg.user.username,
        'timestamp': format_timestamp(msg.timestamp),
        'is_own': msg.user_id == current_user.id
    } for msg in messages])


# Session routes
@sessions_bp.route('/create/<int:group_id>', methods=['GET', 'POST'])
@login_required
def create(group_id):
    if not check_group_admin(current_user.id, group_id):
        flash('Only group admin can create sessions.')
        return redirect(url_for('groups.details', id=group_id))

    group = StudyGroup.query.get_or_404(group_id)
    form = SessionForm()

    if form.validate_on_submit():
        session = StudySession(
            group_id=group_id,
            date=form.date.data,
            location=form.location.data,
            description=form.description.data
        )
        db.session.add(session)
        db.session.commit()
        flash('Study session scheduled successfully!')
        return redirect(url_for('groups.details', id=group_id))

    return render_template('sessions/create.html', form=form, group=group)


@sessions_bp.route('/<int:session_id>/delete', methods=['POST'])
@login_required
def delete_session(session_id):
    session = StudySession.query.get_or_404(session_id)

    if not check_group_admin(current_user.id, session.group_id):
        flash('Only group admin can delete sessions.')
        return redirect(url_for('groups.details', id=session.group_id))

    db.session.delete(session)
    db.session.commit()
    flash('Study session has been deleted.')
    return redirect(url_for('groups.details', id=session.group_id))


@sessions_bp.route('/<int:session_id>/rsvp', methods=['POST'])
@login_required
def rsvp(session_id):
    session = StudySession.query.get_or_404(session_id)

    if not check_group_membership(current_user.id, session.group_id):
        return jsonify({'error': 'You must be a group member to RSVP'}), 403

    status = request.form.get('status')
    if status not in ['going', 'not_going', 'maybe']:
        return jsonify({'error': 'Invalid RSVP status'}), 400

    comment = request.form.get('comment', '').strip()
    rsvp = SessionRSVP.query.filter_by(
        session_id=session_id,
        user_id=current_user.id
    ).first()

    if rsvp:
        rsvp.status = status
        rsvp.comment = comment
        rsvp.timestamp = datetime.now(timezone.utc)
    else:
        rsvp = SessionRSVP(
            session_id=session_id,
            user_id=current_user.id,
            status=status,
            comment=comment
        )
        db.session.add(rsvp)

    db.session.commit()
    return jsonify({
        'status': 'success',
        'counts': session.get_rsvp_counts(),
        'message': f'You are {status} to this session'
    })


@sessions_bp.route('/<int:session_id>/rsvps')
@login_required
def get_rsvps(session_id):
    session = StudySession.query.get_or_404(session_id)

    if not check_group_membership(current_user.id, session.group_id):
        return jsonify({'error': 'Access denied'}), 403

    rsvps = SessionRSVP.query.filter_by(session_id=session_id) \
        .order_by(SessionRSVP.timestamp.desc()).all()

    return jsonify([{
        'id': rsvp.id,
        'user': rsvp.user.username,
        'status': rsvp.status,
        'comment': rsvp.comment,
        'timestamp': format_timestamp(rsvp.timestamp)
    } for rsvp in rsvps])