import json
import os
from datetime import datetime
from uuid import UUID

import aio_pika


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, UUID):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


async def publish_alert_email(device_id: str, voltage: float, timestamp: str):
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")
    connection = await aio_pika.connect_robust(rabbitmq_url)
    async with connection:
        channel = await connection.channel()
        await channel.declare_queue("alert_emails", durable=True)
        message_body = json.dumps(
            {"deviceId": device_id, "voltage": voltage, "time": timestamp},
            cls=DateTimeEncoder,
        ).encode()
        await channel.default_exchange.publish(
            aio_pika.Message(body=message_body),
            routing_key="alert_emails",
        )
