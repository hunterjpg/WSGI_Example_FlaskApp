# Main Routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app
from flask_login import current_user, fresh_login_required, login_required, login_user, logout_user
from sqlalchemy.orm import undefer
from .util import JinjaUtils, ordinal
from .database import (db, guestbook_by_id, all_guestbooks, select, get_hitcount,
                        increment_hitcount, get_banned_ips, GuestbookEntry,
                        ban_ip, unban_ip, recent_guestbooks, BannedAddress, User)
from .forms import GuestbookForm, LoginForm, AdminRemoveForm, AdminBanForm, AdminUnbanForm
from wtforms import ValidationError

#DEFAULT_PROFILE_IMAGE = 'static/img/profile_default.png'

bp = Blueprint('main', __name__) #template_folder=f'../templates/auth'

@bp.route('/', methods=['GET'])
def index():
    increment_hitcount()
    hitcount = f"You are the {ordinal(get_hitcount())} visitor!"
    return render_template('index.html', hitcount=hitcount)


@bp.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    guestbooks = all_guestbooks(paginate=False)
    return render_template('guestbook.html', guestbooks=guestbooks)


@bp.route('/guestbook&t=sign', methods=['GET', 'POST'])
def sign_guestbook():
    banned_ips = get_banned_ips(ip_list=True)
    if request.remote_addr in banned_ips:
        abort(403)
    form = GuestbookForm()

    # if request.method == 'POST':
    if form.validate_on_submit():
        entry = GuestbookEntry()
        if form.name.data:
            entry.name      = form.name.data
            entry.message   = form.message.data # type: ignore
            entry.ip        = str(request.remote_addr)
        else:
            db.session.rollback()
            flash("There was an issue with the submission.<br>Please try deleting your browser cookies and try again.",
                JinjaUtils.ERROR)
            return render_template('sign_guestbook.html', form=form)
        db.session.add(entry)
        db.session.commit()
        current_app.logger.info(f'New Guestbook:\n\tName: {form.name.data}\n\tIP: {request.remote_addr}\n\tMessage:\n{form.message.data}')
        flash(f"Thank you for signing our guestbook!<br>Click <a href='{url_for('main.index')}'>here</a> to go back home.")
        return redirect(url_for('main.guestbook'))
    elif request.method == 'GET':
        return render_template('sign_guestbook.html', form=form)
    else:
        errs = form.errors.get('name')
        if errs:
            flash(','.join(errs), JinjaUtils.ERROR)
        else:
            flash('There was an issue with your submission!<br>Please try again.', JinjaUtils.ERROR)
        # return redirect(url_for('main.sign_guestbook'))
        # if form.form_errors:
            #     for err in form.form_errors:
            #         flash(err, JinjaUtils.ERROR)
    
    return render_template('sign_guestbook.html', form=form)


# --- Login/Logout--- #
@bp.route('/login', methods=['GET', 'POST'])
def login(next: str = ''):
    '''Present login form and accept multipart form POST.  
    Login user and set the `is_logged_in` flag to `True` on successful authentication'''
    # TODO: Allow login via email, if present
    form = LoginForm()
    if request.method == 'GET':
        if current_user.is_authenticated:
            return redirect(url_for('main.index'))
    else:
        if form.validate_on_submit():
            user: User
            try:
                stmt = select(User).where(User.name == form.username.data).options(undefer(User.password_hash))
                user = db.session.execute(stmt).scalar_one()
                if not user:
                    raise
            except:
                flash("Username is Incorrect", category=JinjaUtils.ERROR)
                current_app.logger.info(f'User failed login by username: Name: {form.username.data}.')
                return render_template('auth/login.html', form=form)
            pw = form.password.data
            if not pw:
                flash("Password is Incorrect", category=JinjaUtils.ERROR)
                current_app.logger.info(f'User failed login by password: Name: {form.username.data}.')
            elif user and user.check_password(pw):
                login_user(user, remember=form.rememberme.data)
                user.is_logged_in = True
                db.session.commit()
                flash(f"Logged in as {form.username.data}!", category=JinjaUtils.SUCCESS)
                current_app.logger.info(f'User logged in: Name: {user.name}; ID: {user.id}.')
                _next = request.args.get("next")
                return redirect(_next if _next else url_for("main.admin"))
            else:
                flash("Password is Incorrect", category=JinjaUtils.ERROR)
                current_app.logger.info(f'User failed login by password: Name: {form.username.data}.')
    return  render_template('login.html', form=form)


@login_required
@bp.route('/logout')
def logout():
    '''Log out current user and set the `is_logged_in` flag to `False`.'''
    current_user.is_logged_in = False
    db.session.commit()
    logout_user()
    return redirect(url_for('main.index'))
# --- ----- --- #

# --- Admin --- #
@fresh_login_required
@bp.route('/admin', methods=['GET'])
def admin():
    if not current_user.is_authenticated:
        flash('Not logged in', JinjaUtils.ERROR)
        abort(403)
    
    guestbooks = all_guestbooks(paginate=False)
    banned_ips = get_banned_ips()
    remove_form = AdminRemoveForm()
    ban_form = AdminBanForm()
    unban_form = AdminUnbanForm()
    
    return render_template('admin.html', 
                           guestbooks=guestbooks,
                           banned_ips=banned_ips,
                           remove_form=remove_form,
                           ban_form=ban_form,
                           unban_form=unban_form
                           )


@login_required
@bp.route('/admin&t=remove', methods=['POST'])
def admin_remove():
    # Hacky user validation
    # if request.remote_addr is not '192.168.224.254':
    #     abort(403)
    
    form = AdminRemoveForm(request.form)

    if form.validate_on_submit():
        entry = guestbook_by_id(int(form.id.data)) # type: ignore
        if (not form.id.data) or (not entry):
            flash("There was an issue with the ID. Try again.", JinjaUtils.ERROR)
            return redirect(url_for('main.admin'))
        db.session.delete(entry)
        db.session.commit()
        current_app.logger.info(f'Guestbook Deleted:\tID: {form.id.data}\n\tName: {entry.name}')
        flash(f"Entry Deleted!")
    return redirect(url_for('main.admin'))


@login_required
@bp.route('/admin&t=ban', methods=['POST'])
def admin_ban():
    if not current_user.is_authenticated:
        flash('Not logged in', JinjaUtils.ERROR)
        abort(403)
    
    form = AdminBanForm(request.form)

    if form.validate_on_submit():
        ban_ip(str(form.ip.data))
        current_app.logger.info(f'IP Banned:\tIP: {form.ip.data}')
        flash(f"IP &nbsp;'<code>{form.ip.data}</code>'&nbsp; Banned!")
    return redirect(url_for('main.admin'))


@login_required
@bp.route('/admin&t=unban', methods=['POST'])
def admin_unban():
    if not current_user.is_authenticated:
        flash('Not logged in', JinjaUtils.ERROR)
        abort(403)
    
    form = AdminUnbanForm(request.form)

    if form.validate_on_submit():
        unban_ip(str(form.ip.data))
        current_app.logger.info(f'IP Unbanned:\tIP: {form.ip.data}')
        flash(f"IP &nbsp;'<code>{form.ip.data}</code>'&nbsp; Unbanned!")
    return redirect(url_for('main.admin'))