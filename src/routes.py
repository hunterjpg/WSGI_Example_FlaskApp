# Main Routes

from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app
from .util import JinjaUtils
from .database import db, guestbook_by_name, all_guestbooks, increment_hitcount, recent_guestbooks, GuestbookEntry
from .forms import GuestBookForm

#DEFAULT_PROFILE_IMAGE = 'static/img/profile_default.png'

bp = Blueprint('main', __name__) #template_folder=f'../templates/auth'

@bp.route('/', methods=['GET'])
def index():
    increment_hitcount()
    return render_template('index.html')


@bp.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    guestbooks = all_guestbooks(False)
    return render_template('guestbook.html', guestbooks=guestbooks)


@bp.route('/guestbook?t=sign', methods=['GET', 'POST'])
def sign_guestbook():
    form = GuestBookForm(request.values)

    if request.method == 'POST':
        if form.validate_on_submit():
            # print(f'User_ID={form.user_id.data}')
            # print(f'Is_int={isinstance(form.user_id.data, int)}')
            # print(f'Category={form.category.data}')
            # print(f'Description={form.description.data}')
            entry = GuestbookEntry()
            if form.name.data:
                entry.name      = form.name.data
                entry.message   = form.message.data
                entry.ip        = str(request.remote_addr)
            else:
                db.session.rollback()
                flash("There was an issue with the submission.<br>Please try deleting your browser cookies and try again.",
                    JinjaUtils.ERROR)
                return render_template('sign_guestbook.html', form=form)
            db.session.add(entry)
            db.session.commit()
            current_app.logger.info(f'New Guestbook:\n\tName: {form.name.data}\n\tIP: {request.remote_addr}.')
            flash(f"Thank you for signing our guestbook!<br>Click <a href='{url_for('main.index')}'>here</a> to go back home.")
            return redirect(url_for('main.guestbook'))
        elif form.form_errors:
            for err in form.form_errors:
                flash(err, JinjaUtils.ERROR)
    return render_template('sign_guestbook.html', form=form)