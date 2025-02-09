from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy.exc import SQLAlchemyError
from src.db.models import Base, Subscription
from src.logger import logger
import os
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


async def init_db():
    """Инициализация базы данных (создание таблиц, если их нет)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database initialized successfully!")


async def get_db():
    """Асинхронный генератор сессии."""
    async with AsyncSessionLocal() as session:
        yield session


class SubscriptionModel:
    @staticmethod
    async def create_subscription(session: AsyncSession, name, password, tariff, payment_method, price, created_time,
                                  next_pay_time):
        """Создание новой подписки."""
        new_subscription = Subscription(
            name=name,
            password=password,
            tariff=tariff,
            payment_method=payment_method,
            price=price,
            created_time=created_time,
            next_pay_time=next_pay_time
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
