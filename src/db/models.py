from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime

Base = declarative_base()


class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)  # Логин пользователя
    password = Column(String, nullable=False)
    telegram_username = Column(String, nullable=False)
    payment_method = Column(String, nullable=False)  # "card" или "sbp"
    tariff = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    created_time = Column(DateTime, nullable=False)
    next_pay_time = Column(DateTime, nullable=False)
    screenshot = Column(String, nullable=True)  # Путь к файлу скриншота
