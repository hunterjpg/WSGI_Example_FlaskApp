# Main Routes

from datetime import datetime, timezone, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, abort, current_app
from werkzeug import Response
from sqlalchemy import select
from sqlalchemy.orm import undefer_group
#
from .util import JinjaUtils
from .database import db, guestbook_by_name, GuestbookEntry
from .forms import GuestBookForm

#DEFAULT_PROFILE_IMAGE = 'static/img/profile_default.png'

bp = Blueprint('main', __name__) #template_folder=f'../templates/auth'

@bp.route('/', methods=['GET'])
def index():
    # Increment hitcounter
    # Show
    
    return render_template('index.html')

@bp.route('/guestbook', methods=['GET', 'POST'])
def guestbook():
    form = GuestBookForm(request.values)
    if form.validate_on_submit():
        # print(f'User_ID={form.user_id.data}')
        # print(f'Is_int={isinstance(form.user_id.data, int)}')
        # print(f'Category={form.category.data}')
        # print(f'Description={form.description.data}')
        entry = GuestbookEntry()
        if form.name.data:
            entry.name     = form.name.data
            entry.message  = form.message.data
        else:
            db.session.rollback()
            flash("There was an issue with the submission.<br>Please try deleting your browser cookies and try again.",
                  JinjaUtils.ERROR)
            return render_template('guestbook.html', form=form)
        db.session.add(entry)
        db.commit()
        flash(f"Thank you for signing our guestbook!<br>Click <a href='{url_for('main.index')}'>here</a> to go back home.")
    return render_template('guestbook.html', form=form)