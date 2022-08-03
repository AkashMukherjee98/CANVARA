from contextlib import contextmanager

from sqlalchemy import engine_from_config
from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.orm import Session

import backend.common.config

ModelBase = declarative_base(cls=DeferredReflection)


class CanvaraDB:
    __engine = None

    @classmethod
    def get_engine(cls):
        if cls.__engine is None:
            canvara_config = backend.common.config.get_canvara_config()
            cls.__engine = engine_from_config(canvara_config['database'], prefix="sqlalchemy.")
        return cls.__engine

    @classmethod
    def init_db(cls):  # pylint: disable=too-many-locals
        # pylint: disable=cyclic-import, import-outside-toplevel, unused-import
        from .project import Project            # noqa: F401
        from .client import Client              # noqa: F401
        from .offer import Offer, OfferProposal     # noqa: F401
        from .position import Position          # noqa: F401
        from .community import Community        # noqa: F401
        from .event import Event                # noqa: F401
        from .application import Application    # noqa: F401
        from .customer import Customer          # noqa: F401
        from .feedback import Feedback          # noqa: F401
        from .location import Location          # noqa: F401
        from .match import UserPostMatch        # noqa: F401
        from .notification import Notification  # noqa: F401
        from .performer import Performer        # noqa: F401
        from .post import Post, PostSkill, UserPostBookmark, UserPostLike  # noqa: F401
        from .post_type import PostType         # noqa: F401
        from .product_preference import ProductPreference           # noqa: F401
        from .skill import Skill                # noqa: F401
        from .user import User, UserCurrentSkill, UserDesiredSkill  # noqa: F401
        from .backgroundpicture import BackgroundPicture    # noqa: F401
        from .user_upload import UserUpload     # noqa: F401
        from .share import Share                # noqa: F401
        from .activities import Activity        # noqa: F401
        # pylint: enable=cyclic-import, import-outside-toplevel, unused-import

        engine = cls.get_engine()
        ModelBase.prepare(engine)


# Helpful context manager that manages the Session lifecycle
@contextmanager
def transaction():
    session = Session(CanvaraDB.get_engine(), expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
