from contextlib import contextmanager

from sqlalchemy import engine_from_config, MetaData
from sqlalchemy.orm import declarative_base, Session

import backend.common.config

ModelBase = declarative_base()


class CanvaraDB:  # pylint: disable=too-few-public-methods
    def __init__(self):
        canvara_config = backend.common.config.get_canvara_config()
        self.engine = engine_from_config(canvara_config['database'], prefix="sqlalchemy.")

        self.metadata = MetaData(self.engine)
        self.metadata.reflect()


db = CanvaraDB()


# Helpful context manager that manages the Session lifecycle
@contextmanager
def transaction():
    session = Session(db.engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
