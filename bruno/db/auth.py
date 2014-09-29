# from bruno.db import db_session as session
from bruno.env import inputs


def login(socket, user):
    """
        login(socket, user) -> None

        Sets user.online to True and inputs[socket].profile to user
    """
    if user.online is False:
        inputs[socket].profile = user
        user.online = True
        user.save()
    else:
        return 1


def logout(socket, user=None):
    """
        logout(socket, user) -> None

        Sets user.online to False and inputs[socket].profile to None
    """
    if not user:
        user = inputs[socket].profile
    inputs[socket].profile = None
    user.online = False
    user.save()
