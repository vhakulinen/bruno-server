import uuid
import hashlib

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

# from bruno.db import Base, db_session as session
from bruno.db.constants import Base, db_session as session


# For friendships
association_table = Table("association", Base.metadata,
                          Column("user_id", Integer, ForeignKey("user.id"),
                                 primary_key=True),
                          Column("friend_id", Integer, ForeignKey("user.id"),
                                 primary_key=True),
                          )


# For friendship requests
request_table = Table("requests", Base.metadata,
                      Column("user_id", Integer, ForeignKey("user.id"),
                             primary_key=True),
                      Column("target_id", Integer, ForeignKey("user.id"),
                             primary_key=True),
                      )


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    _username = Column(String(30), nullable=False, unique=True)
    password = Column(String(60), nullable=False)
    online = Column(Boolean, default=False)
    # peer2peer = Column(Boolean, default=True)

    friends = relationship("User", secondary=association_table,
                           primaryjoin=id == association_table.c.user_id,
                           secondaryjoin=id == association_table.c.friend_id)
    requests = relationship("User", secondary=request_table,
                            primaryjoin=id == request_table.c.user_id,
                            secondaryjoin=id == request_table.c.target_id)

    def __init__(self, username, password, *args, **kwargs):
        salt = uuid.uuid4().bytes
        password = salt+hashlib.sha256(password.encode('utf8') + salt).digest()
        super().__init__(username=username, password=password, *args, **kwargs)

    @hybrid_property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if len(value) < 3:
            raise ValueError('Min lenght is 3')
        self._username = value

    def valid_password(self, password):
        salt = self.password[:16]
        if self.password[16:] ==\
           hashlib.sha256(password.encode('utf8')+salt).digest():
            return True
        else:
            False

    def save(self):
        session.add(self)
        session.commit()
