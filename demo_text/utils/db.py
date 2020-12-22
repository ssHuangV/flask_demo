
import contextlib

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from settings import Config


class DBManager(object):

    def __init__(self):
        self.master_session = None
        self.create_sessions()

    def create_sessions(self):
        self.master_session = self.create_single_session(
            Config.MASTER_DATABASE_URI)

    @classmethod
    def create_single_session(cls, url, scopefunc=None):
        engine = create_engine(url, echo=False)
        session_factory = sessionmaker(expire_on_commit=True, bind=engine)
        Session = scoped_session(session_factory, scopefunc=scopefunc)
        return Session

    def get_session(self):
        if self.master_session:
            return self.master_session
        else:
            raise IndexError('cannot get master_session from DB_SETTING')

    @contextlib.contextmanager
    def session_ctx(self):
        DBSession = self.get_session()
        session = DBSession()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise
        finally:
            session.expunge_all()
            session.close()
