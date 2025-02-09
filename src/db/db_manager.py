from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from src.db.models import Base, Subscription
from src.logger import logger
import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")

DATABASE_URL = f'postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

logger.info(f"Connecting to database: {DATABASE_URL}")

engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def create_database():
    """Создает базу данных, если она не существует."""
    conn = await asyncpg.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, database="postgres")
    db_exists = await conn.fetchval(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")

    if not db_exists:
        await conn.execute(f'CREATE DATABASE "{DB_NAME}" OWNER {DB_USER}')
        logger.info(f"База данных {DB_NAME} создана.")
    else:
        logger.info(f"База данных {DB_NAME} уже существует.")

    await conn.close()


async def init_db():
    """Инициализация базы данных: создаёт, если нет, и обновляет схему."""
    await create_database()

    async with engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
            logger.info("Схема базы данных обновлена.")
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при создании таблиц: {e}")


async def get_db():
    """Асинхронный генератор сессии."""
    async with AsyncSessionLocal() as session:
        yield session


class SubscriptionModel:
    @staticmethod
    async def create_subscription(session: AsyncSession, name, password, tariff, payment_method, price, created_time,
                                  next_pay_time, screenshot, telegram_username):
        """Создание новой подписки."""
        new_subscription = Subscription(
            name=name,
            password=password,
            telegram_username=telegram_username,
            tariff=tariff,
            payment_method=payment_method,
            price=price,
            created_time=created_time,
            next_pay_time=next_pay_time,
            screenshot=screenshot
        )
        try:
            session.add(new_subscription)
            await session.commit()
            return new_subscription
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error(f"Ошибка при создании подписки: {e}")
            return None

    @staticmethod
    async def get_subscription_by_id(session: AsyncSession, subscription_id: int):
        """Получение подписки по ID."""
        try:
            result = await session.execute(select(Subscription).filter(Subscription.id == subscription_id))
            return result.scalars().first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении подписки: {e}")
            return None

    @staticmethod
    async def get_all_subscriptions(session: AsyncSession):
        """Получение всех подписок."""
        try:
            result = await session.execute(select(Subscription))
            return result.scalars().all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении всех подписок: {e}")
            return []
