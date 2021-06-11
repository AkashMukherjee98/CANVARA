from contextlib import contextmanager

from sqlalchemy import engine_from_config, MetaData
from sqlalchemy.orm import declarative_base, Session

import common.config

ModelBase = declarative_base()

class CanvaraDB:
    def __init__(self):
        canvara_config = common.config.get_canvara_config()
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
    except:
        session.rollback()
        raise
    finally:
        session.close()
