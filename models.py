from sqlalchemy import Integer, Column
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    uid = Column(Integer, primary_key=True)
    tid = Column(Integer)
    gid = Column(Integer, nullable=True)
    vid = Column(Integer, nullable=True)
    last_task = Column(Integer, nullable=True)