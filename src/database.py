'''DB object definitions for SQLAlchemy with sqlite'''

from flask import abort
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from flask_login import UserMixin, AnonymousUserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import ForeignKey, String, select, DateTime, UniqueConstraint, asc, desc
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, defer, undefer, relationship, selectin_polymorphic
from sqlalchemy.ext.declarative import declared_attr
from werkzeug.security import generate_password_hash, check_password_hash

# ---- BASE MODEL and DB SETUP---- #
class Base(DeclarativeBase):
    '''Declaritive base class for models'''
    pass
db = SQLAlchemy(model_class=Base)


class AnonymousUser(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Anonymous'
        self.name = 'Anonymous'

# ---- CUSTOM MIXINS ---- #
class TimestampMixin:
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   default=datetime.now(timezone.utc))
    updated_date: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   onupdate=datetime.now(timezone.utc),
                                                   default=datetime.now(timezone.utc),
                                                   deferred=True)


# GUESTBOOK
class GuestbookEntry(db.Model, TimestampMixin):
    '''Public guestbook'''
    __tablename__ = 'guestbook_entry'
    id:         Mapped[int] = mapped_column(primary_key=True, unique=True, autoincrement=True)
    name:       Mapped[str] = mapped_column(String(32))
    message:    Mapped[str] = mapped_column(String(255))
    ip:         Mapped[str] = mapped_column(String(12))


# METADATA
class MetaData(db.Model):
    '''Sitewide Metadata Table for totals.  
    Use default ID 1 or `.first()`
    '''
    id:         Mapped[int]     = mapped_column(primary_key=True)
    hitcount:   Mapped[int]     = mapped_column(nullable=True, default=0, deferred=True, deferred_group='meta')
    seeded:     Mapped[bool]    = mapped_column(nullable=True, default=False, deferred=True, deferred_group='meta')

    def __str__(self):
        return f'id={self.id}\nhitcount={self.hitcount}\nseeded={self.seeded}'
    
    def setup_meta(self):
        '''Create one entry in the metadata table if none exist'''
        if not MetaData.query.first():
            meta = self
            meta.seeded = False
            meta.hitcount = 0
            db.session.add(meta)
            db.session.commit()
            m = db.session.query(MetaData).first()
            print(f'Metadata: Single entry created:\n{m}') 

# # ADMIN

class User(UserMixin, TimestampMixin, db.Model):
    '''Base `User` model.
    Deferred groups: 'login', 'metadata', 'forum' '''
    __tablename__ = 'user'
    id:             Mapped[int]         = mapped_column(primary_key=True, unique=True)
    name:           Mapped[str]         = mapped_column(String(24), unique=True)
    password_hash:  Mapped[str]         = mapped_column(String(128), nullable=False, deferred=True)
    is_logged_in:   Mapped[bool]        = mapped_column(default=False)

    def get(self) -> User:
        return self
    
    def get_id(self) -> int:
        return self.id
    
    def get_name(self) -> str:
        return self.name

    def set_password(self, password: str | None):
        if not password:
            raise ValueError("password must be a valid 'str'")
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        '''Is the user logged in'''
        return super().is_authenticated
    
    @property
    def is_active(self):
        '''Is the user valid (activated, not deactivated) and able to log in'''
        # Returns false if this user is banned or deleted, disallowing logins
        return super().is_active
    
    @property
    def is_anonymous(self):
        return super().is_anonymous
    


class BannedAddress(db.Model, TimestampMixin):
    '''Banned IP/MAC Addresses'''
    __tablename__ = 'banned_address'
    id:         Mapped[int]     = mapped_column(primary_key=True, autoincrement=True)
    ip:         Mapped[str]     = mapped_column(String(12), unique=True, nullable=False) #,nullable=True)
    # mac:        Mapped[str]     = mapped_column(String(17), nullable=True, unique=True)


# ---- Query Funcs ---- #

# -- Admin -- #
# IP
def ban_ip(ip: str):
    banned = BannedAddress()
    banned.ip = ip
    db.session.add(banned)
    db.session.commit()

def unban_ip(ip: str):
    stmt = select(BannedAddress).where(BannedAddress.ip == ip)
    banned_ip = db.session.execute(stmt).scalar_one_or_none()
    if not banned_ip:
        return
    db.session.delete(banned_ip)
    db.session.commit()

def get_banned_ips(ip_list: bool = False):
    if ip_list:
        stmt = select(BannedAddress.ip)#.where(BannedAddress.ip != None)
    else:    
        stmt = select(BannedAddress).order_by(BannedAddress.id)#.where(BannedAddress.ip != None)
    return db.session.execute(stmt).scalars().all()

# MAC
# def ban_mac(mac: str):
#     banned = BannedAddress()
#     banned.mac = mac
#     db.session.add(banned)
#     db.session.commit()

# def unban_mac(mac: str):
#     stmt = select(BannedAddress).where(BannedAddress.mac == mac)
#     banned_mac = db.session.execute(stmt).scalar_one_or_none()
#     if not banned_mac:
#         return
#     db.session.delete(banned_mac)
#     db.session.commit()

# def get_banned_macs():
#     stmt = select(BannedAddress).where(BannedAddress.mac != None)
#     return db.session.execute(stmt).scalars().all()



# - MetaData - #
def get_meta() -> MetaData:
    '''Return the entire metadata table
    Raises:
        Exception if the row is not present
    Returns:
        MetaData: The first (and only) row in the MetaData table
    '''
    return db.session.execute(select(MetaData)).scalar_one()

def get_hitcount() -> int:
    stmt = select(MetaData.hitcount)
    return db.session.execute(stmt).scalar_one()


def increment_hitcount():
    # m = db.session.query(MetaData).options(undefer(MetaData.hitcount)).first()
    m = db.session.execute(
        select(MetaData).options(undefer(MetaData.hitcount))
        ).scalar_one()
    m.hitcount = m.hitcount + 1 # Can't += on columns
    db.session.commit()


# -- Guestbook -- #
def all_guestbooks():
    '''All guestbook entries sorted by date, optionally paginated'''
    stmt = select(GuestbookEntry).order_by(GuestbookEntry.id)
    return db.session.execute(stmt).scalars().all()

def recent_guestbooks(n: int):
    '''Top `n` most recent guestbook entries'''
    stmt = select(GuestbookEntry).order_by(GuestbookEntry.created_date).limit(n)
    return db.session.execute(stmt).scalars().fetchmany(n)


def guestbook_by_id(id: int | None) -> GuestbookEntry | None:
    '''Return one GuestbookEntry matching `GuestbookEntry.id` or None'''
    if not id: return None
    stmt = select(GuestbookEntry).where(GuestbookEntry.id == id)
    return db.session.execute(stmt).scalar()


def guestbook_by_name(name: str | None) -> GuestbookEntry | None:
    '''Return one GuestbookEntry with a matching `name` or None'''
    if not name: return None
    stmt = select(GuestbookEntry).filter_by(name=name)
    return db.session.execute(stmt).scalar()


def guestbook_name_or_404(name: str | None):
    '''Return one GuestbookEntry with a matching `name` or abort with a 404'''
    description = f"We couldn't find an entry with the name '{name}'!"
    if not name: abort(404, description=description)
    stmt = select(GuestbookEntry).where(GuestbookEntry.name == name)
    return db.one_or_404(stmt, description=description)