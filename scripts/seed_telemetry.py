import asyncio
import random

import httpx

API_URL = "http://127.0.0.1:8000/api/v1/telemetry/"
NUM_RECORDS = 50


async def seed_data():
    print(f"Starting to send {NUM_RECORDS} telemetry records...")
    async with httpx.AsyncClient() as client:
        for i in range(1, NUM_RECORDS + 1):
            payload = {
                "device_id": f"pico-0{random.randint(1, 3)}",
                "voltage": round(random.uniform(3.1, 3.5), 2),
                "current": round(random.uniform(0.3, 0.8), 2),
            }
            res = await client.post(API_URL, json=payload)
            if res.status_code == 201:
                data = res.json()
                print(
                    f"[{i}/{NUM_RECORDS}] Sent {payload['device_id']}: Voltage={payload['voltage']}V, Current={payload['current']}A -> Created (ID: {data['id']})"
                )
            else:
                print(f"[{i}/{NUM_RECORDS}] Error: {res.status_code} - {res.text}")
            await asyncio.sleep(0.02)
    print("\nCompleted sending all records successfully!")


if __name__ == "__main__":
    asyncio.run(seed_data())
