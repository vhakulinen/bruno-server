# from sqlalchemy.ext.declarative import declarative_base
from include.db.constants import engine, Base, db_session as session
from include.db.models import User


def get_user(username):
    """
        get_user(username) -> User or None

        Returns models.User object if user exists else None.
    """
    query = session.query(User).filter(User.username == username)
    if query.count() == 0:
        return None
    else:
        return query.one()


def create_user(username, password):
    """
        create_user(username, password) -> User

        Creates new user and returns User object of newly created user.
    """
    new_user = User(username=username, password=password)
    new_user.save()
    return new_user


def init_db():
    import include.db.models
    Base.metadata.create_all(engine)
