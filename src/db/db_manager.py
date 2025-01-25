from datetime import datetime
from src.db.models import Subscription, session


class SubscriptionModel:
    @staticmethod
    def create_subscription(name, password, tariff, payment_method, price, created_time, next_pay_time):
        new_subscription = Subscription(
            name=name,
            password=password,
            tariff=tariff,
            payment_method=payment_method,
            price=price,
            created_time=created_time,
            next_pay_time=next_pay_time
        )
        session.add(new_subscription)
        session.commit()
        return new_subscription

    @staticmethod
    def get_subscription_by_id(subscription_id):
        return session.query(Subscription).filter(Subscription.id == subscription_id).first()

    @staticmethod
    def get_all_subscriptions():
        return session.query(Subscription).all()
