from sqlalchemy import Column, BigInteger, String, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class User(Base):
    __tablename__ = "t_users"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    user_id = Column(BigInteger)
    s_username = Column(String(50))
    s_firstname = Column(String(50))
    s_lastname = Column(String(50))
    s_language_code = Column(String(5))
    s_is_premium = Column(String(5))
    dt_dateupd = Column(DateTime)

    def __repr__(self) -> str:
        return (f"User("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"s_username={self.s_username}, "
                f"s_firstname={self.s_firstname}, "
                f"s_lastname={self.s_lastname}, "
                f"s_language_code={self.s_language_code}, "
                f"s_is_premium={self.s_is_premium}, "
                f"dt_dateupd={self.dt_dateupd}"
                f")")


class Log(Base):
    __tablename__ = "t_log"

    id = Column(BigInteger, primary_key=True, unique=True, autoincrement=True)
    user_id = Column(BigInteger)
    s_username = Column(String(50))
    s_firstname = Column(String(50))
    s_lastname = Column(String(50))
    s_language_code = Column(String(5))
    s_is_premium = Column(String(5))
    s_question = Column(String(100))
    s_answer = Column(String(1000))
    dt_dateupd = Column(DateTime)

    def __repr__(self) -> str:
        return (f"Log("
                f"id={self.id}, "
                f"user_id={self.user_id}, "
                f"s_username={self.s_username}, "
                f"s_firstname={self.s_firstname}, "
                f"s_lastname={self.s_lastname}, "
                f"s_language_code={self.s_language_code}, "
                f"s_is_premium={self.s_is_premium}, "
                f"s_question={self.s_question}, "
                f"s_answer={self.s_answer}, "
                f"dt_dateupd={self.dt_dateupd}"
                f")")


class Client(Base):
    __tablename__ = "t_client"

    user_id = Column(BigInteger, primary_key=True, unique=True, autoincrement=False)
    s_username = Column(String(50))
    s_firstname = Column(String(50))
    s_lastname = Column(String(50))
    s_language_code = Column(String(5))
    s_is_premium = Column(String(5))
    s_survey = Column(Text)
    s_psyco = Column(String(50))
    s_tech = Column(String(50))
    dt_dateupd = Column(DateTime)

    def __repr__(self) -> str:
        return (f"Client("
                f"user_id={self.user_id}, "
                f"s_username={self.s_username}, "
                f"s_firstname={self.s_firstname}, "
                f"s_lastname={self.s_lastname}, "
                f"s_language_code={self.s_language_code}, "
                f"s_is_premium={self.s_is_premium}, "
                f"s_survey={self.s_survey}, "
                f"s_psyco={self.s_psyco}, "
                f"s_tech={self.s_tech}, "
                f"dt_dateupd={self.dt_dateupd}"
                f")")
