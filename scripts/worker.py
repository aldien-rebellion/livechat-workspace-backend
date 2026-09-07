import asyncio
import json
import os

import aio_pika


async def main():
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@127.0.0.1:5672/")
    connection = await aio_pika.connect_robust(rabbitmq_url)

    async with connection:
        channel = await connection.channel()
        # To make sure load is distributed evenly
        await channel.set_qos(prefetch_count=1)

        queue = await channel.declare_queue("alert_emails", durable=True)

        print(" [*] Waiting for messages. To exit press CTRL+C")

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    # Parse JSON body
                    body = json.loads(message.body.decode())
                    device_id = body.get("deviceId")
                    print(
                        f" [x] Received Alert from {device_id}. "
                        "Sending email to admin..."
                    )
                    # Simulate delay
                    await asyncio.sleep(3)
                    print(" [v] Email sent successfully!")


if __name__ == "__main__":
    asyncio.run(main())
