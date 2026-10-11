'''Login Manager and loader setup for Flask-Login'''

from flask import Request
from flask_login import LoginManager

login_manager = LoginManager()

from .database import User, select, db #, File, ImageFile, UserData, ForumPost, File, RegistrationKey,

@login_manager.user_loader
def user_loader(user_id) -> User | None:
    user: User | None
    try:
        user = db.session.execute(select(User).where(User.id == user_id)).scalar_one()
    except:
        return
    return user


@login_manager.request_loader
def request_loader(request: Request) -> User | None:
    request.access_route
    name = request.form.get('username')
    user: User | None
    try:
        user = db.session.execute(select(User).where(User.name == name)).scalar_one()
    except:
        return
    return user
