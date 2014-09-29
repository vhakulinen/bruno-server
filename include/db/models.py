from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Table
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

# from include.db import Base, db_session as session
from include.db.constants import Base, db_session as session


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
                           secondaryjoin=id == association_table.c.friend_id,
                           backref="added_by")
    requests = relationship("User", secondary=request_table,
                            primaryjoin=id == request_table.c.user_id,
                            secondaryjoin=id == request_table.c.target_id,
                            backref="from")

    @hybrid_property
    def username(self):
        return self._username

    @username.setter
    def username(self, value):
        if len(value) < 3:
            raise ValueError('Min lenght is 3')
        self._username = value

    def save(self):
        session.add(self)
        session.commit()
