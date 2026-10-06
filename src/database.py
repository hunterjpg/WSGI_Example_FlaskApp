# DB object definitions

from flask_sqlalchemy import SQLAlchemy
from flask import abort
from sqlalchemy import ForeignKey, String, select, DateTime, UniqueConstraint
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, defer, undefer, relationship, selectin_polymorphic
from sqlalchemy.ext.declarative import declared_attr
from typing import Optional, List


# ---- BASE MODEL and DB SETUP---- #
class Base(DeclarativeBase):
    '''Declaritive base class for models'''
    pass
db = SQLAlchemy(model_class=Base)


# ---- CUSTOM MIXINS ---- #
class TimestampMixin:
    created_date: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                   default=datetime.now(timezone.utc),
                                                   deferred=True)
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


# ---- Query Funcs ---- #

# - MetaData - #
def get_meta() -> MetaData:
    '''Return the entire metadata table
    Raises:
        Exception if the row is not present
    Returns:
        MetaData: The first (and only) row in the MetaData table
    '''
    return db.session.execute(select(MetaData)).scalar_one()


def get_hitcount() -> int | None:
    stmt = select(MetaData.hitcount).options(undefer(MetaData.hitcount))
    return db.session.execute(stmt).scalar()


def increment_hitcount():
    # m = db.session.query(MetaData).options(undefer(MetaData.hitcount)).first()
    m = db.session.execute(
        select(MetaData).options(undefer(MetaData.hitcount))
        ).scalar_one()
    m.hitcount = m.hitcount + 1 # Can't += on columns
    db.session.commit()


# -- Guestbook -- #
def all_guestbooks(paginate: bool = False):
    '''All guestbook entries sorted by date, optionally paginated'''
    stmt = select(GuestbookEntry).order_by(GuestbookEntry.created_date)
    # More info on using a pagination: https://flask-sqlalchemy.readthedocs.io/en/stable/pagination/
    if paginate:
        return db.paginate(stmt)
    return db.session.execute(stmt).scalars().all()

def recent_guestbooks(n: int):
    '''Top `n` most recent guestbook entries'''
    stmt = select(GuestbookEntry).order_by(GuestbookEntry.created_date).limit(n)
    return db.session.execute(stmt).scalars().fetchmany(n)


def guestbook_by_id(id: int | None) -> GuestbookEntry | None:
    '''Return one UserData matching `UserData.id` or None'''
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