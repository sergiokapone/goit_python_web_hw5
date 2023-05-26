import re


def parse(message):

    pattern = r"(exchange)\s*(\d+)?"

    match = re.search(pattern, message)

    if match:
        keyword = match.group(1)  # Слово "exchange"
        number = int(match.group(2)) if match.group(2) else 1
        return keyword, number

    return message, message.strip()


while True:
    message = input(">>> ")
    keyword, number = parse(message)
    if keyword == "exchange":
        print(f"{keyword}: {number}")
    else:
        print(f"keywords: {keyword}")
