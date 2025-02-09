from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()

class Subscription(Base):
    __tablename__ = 'subscriptions'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    password = Column(String)
    payment_method = Column(String)
    tariff = Column(String)
    price = Column(Integer)
    created_time = Column(DateTime)
    next_pay_time = Column(DateTime)
