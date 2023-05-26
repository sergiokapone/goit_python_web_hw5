import asyncio
from datetime import datetime, timedelta
import logging
import re
import aiohttp
import websockets
import names

logging.basicConfig(level=logging.INFO)

BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates"


class Server:
    clients = set()

    async def register(self, ws: websockets.WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: websockets.WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_clients(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: websockets.WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distribute(ws)
        except websockets.exceptions.ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distribute(self, ws: websockets.WebSocketServerProtocol):
        async for message in ws:
            keyword, number = parse(message)
            if keyword == "exchange":
                if number > 10:
                    await self.send_to_clients(
                        f"{ws.name}: Number of days should be less than 10"
                    )
                else:
                    asyncio.create_task(
                        self.process_exchange_request(["USD", "EUR"], number)
                    )
            else:
                await self.send_to_clients(f"{ws.name}: {message}")

    async def process_exchange_request(self, currencies, number):
        result = await fetch_exchange_rates(currencies, number)
        await self.send_to_clients(f"{result}")


async def fetch_exchange_rate(currencies, date):
    async with aiohttp.ClientSession() as session:
        date = date.strftime("%d.%m.%Y")
        url = f"{BASE_URL}?json&date={date}"
        headers = {"Accept": "application/json"}

        async with session.get(url, headers=headers) as response:
            try:
                data = await response.json()
                if "exchangeRate" in data:
                    rates = data["exchangeRate"]
                    v = {}
                    date_rates = {date: v}
                    for rate in rates:
                        if rate["currency"] in currencies:
                            v.update(
                                {
                                    rate["currency"]: {
                                        "sale": rate["saleRate"],
                                        "purchase": rate["purchaseRateNB"],
                                    }
                                }
                            )
                    return date_rates
            except aiohttp.ClientError as e:
                logging.warning(f"Error {e}, when occuring data")


async def fetch_exchange_rates(currencies, days):
    tasks = []
    start_day = datetime.now()
    for i in range(days):
        date = start_day - timedelta(days=i)
        tasks.append(fetch_exchange_rate(currencies, date))

    return await asyncio.gather(*tasks)


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()


def parse(message):
    pattern = r"(exchange)\s*(\d+)?"
    match = re.search(pattern, message)

    if match:
        keyword = match.group(1)
        number = int(match.group(2)) if match.group(2) else 1
        return keyword, number

    return message, ""


if __name__ == "__main__":
    asyncio.run(main())
