from aiofile import async_open
import aiohttp
import asyncio
from datetime import datetime, timedelta
from prettytable import PrettyTable
import argparse


BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates"


async def fetch_exchange_rate(currencies, date):
    async with aiohttp.ClientSession() as session:
        date = date.strftime("%d.%m.%Y")
        url = f"{BASE_URL}?json&date={date}"
        headers = {"Accept": "application/json"}  # Указываем заголовок Accept

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
                print(f"Error {e}, when occcurind data")
                return None


async def fetch_exchange_rates(currencies, days):
    tasks = []
    start_day = datetime.now()
    for i in range(days):
        date = start_day - timedelta(days=i)
        tasks.append(fetch_exchange_rate(currencies, date))

    return await asyncio.gather(*tasks)


async def main(currencies, num_of_days):

    if num_of_days > 10:
        print("Максимальна кількість днів має бути 10.")
        return {}

    exchange_rates = await fetch_exchange_rates(currencies, num_of_days)

    async with async_open("log.txt", mode="a") as log_file:
        await log_file.write(f"exchange {num_of_days}\n")

    return exchange_rates


def build_table(data):

    table = PrettyTable(["Date", "Currency", "Purchase", "Sale"])
    table.align = "l"

    flattened_result = [(date, rates) for item in data for date, rates in item.items()]
    flattened_result.sort(key=lambda x: datetime.strptime(x[0], "%d.%m.%Y"))

    for date, rates in flattened_result:
        row_added = False
        for currency, rate in rates.items():
            purchase = rate["purchase"]
            sale = rate["sale"]
            if not row_added:
                table.add_row([date, currency, f"{purchase:.2f}", f"{sale:.2f}"])
                row_added = True
            else:
                table.add_row(["", currency, f"{purchase:.2f}", f"{sale:.2f}"])

    return table


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--currencies", nargs="*", default=["USD"], help="Currency codes"
    )
    parser.add_argument(
        "-d", "--num_of_days", type=int, default=10, help="Number of days"
    )
    args = parser.parse_args()

    currencies = args.currencies
    num_of_days = args.num_of_days

    result = asyncio.run(main(currencies, num_of_days))
    print(build_table(result))
