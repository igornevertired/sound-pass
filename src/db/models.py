from sqlalchemy import create_engine, Column, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

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

    # Проверяем, существует ли база данных
    if not database_exists(engine.url):
        print("Database does not exist. Creating a new one...")
        create_database(engine.url)
        print("Database created successfully!")
    else:
        print("Database already exists. Connecting to it...")

    # Создаем таблицы, если они не существуют
    Base.metadata.create_all(engine)

    # Создаем сессию
    Session = sessionmaker(bind=engine)
    session = Session()
    print("Connection successful!")

except Exception as e:
    print(f"Connection failed: {e}")