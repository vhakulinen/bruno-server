from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


engine = create_engine('sqlite:///bruno.db')

Base = declarative_base()

DBSession = sessionmaker(bind=engine)
db_session = DBSession()
