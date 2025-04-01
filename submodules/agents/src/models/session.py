"""db session factory"""

import logging
import re

from agents.src.models.config.config import Config
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


class DBSessionFactory:
    """singleton db session factory"""

    _instance = None

    def __new__(cls):
        """singleton instance"""
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """initialize db session factory"""
        conf = Config.get_instance()
        db_url = conf.get("db_url", "db")
        logging.debug(f"connecting to db: db_url={sanitize_db_url(db_url)}")

        if db_url.startswith("sqlite:///:memory:"):
            engine = create_engine(db_url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
        else:
            engine = create_engine(db_url)

        self._session_factory = sessionmaker(bind=engine, autocommit=False, autoflush=False)
        self._engine = engine

    def new_session(self) -> Session:
        """create new session"""
        return self._session_factory()

    def check_health(self):
        """check db connection health"""
        try:
            with self.new_session() as session:
                session.execute("SELECT 1")
                return True, None
        except SQLAlchemyError as err:
            return False, str(err)

    @property
    def engine(self):
        """get sqlalchemy engine"""
        return self._engine

    @classmethod
    def get_instance(cls):
        """get singleton instance"""
        if not cls._instance:
            cls._instance = DBSessionFactory()
        return cls._instance


def sanitize_db_url(url):
    """sanitize db url for logging"""
    return re.sub(r"//.*@", "//****@", url)
