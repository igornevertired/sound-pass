from sqlalchemy import create_engine, Column, Integer, String, DateTime, URL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database

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


DATABASE_URI = 'postgresql+psycopg2://postgres:1353@localhost:5432/dbname'

print(f"Connecting to database: {DATABASE_URI}")

try:
    engine = create_engine(DATABASE_URI)
    create_database(engine.url)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Connection successful!")

except Exception as e:
    print(f"Connection failed: {e}")