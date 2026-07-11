from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

from faker import Faker



CUSTOMERS_COUNT = 10_000
PRODUCTS_COUNT = 1_000
ORDERS_COUNT = 50_000

MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5

RANDOM_SEED = 42

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"


fake = Faker("ru_RU")
Faker.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


CITIES = [
    "Москва",
    "Санкт-Петербург",
    "Казань",
    "Екатеринбург",
    "Новосибирск",
    "Самара",
    "Ростов-на-Дону",
    "Краснодар",
    "Пермь",
    "Уфа",
]

CATEGORIES = {
    "Обувь": [
        "Кроссовки для бега",
        "Кеды",
        "Футбольные бутсы",
        "Треккинговые ботинки",
    ],
    "Одежда": [
        "Спортивная футболка",
        "Худи",
        "Шорты",
        "Спортивные брюки",
        "Ветровка",
    ],
    "Инвентарь": [
        "Гантели",
        "Коврик для йоги",
        "Эспандер",
        "Скакалка",
        "Мяч",
    ],
    "Аксессуары": [
        "Спортивная сумка",
        "Бутылка для воды",
        "Перчатки",
        "Напульсник",
        "Фитнес-резинка",
    ],
}

ORDER_STATUSES = [
    "Завершён",
    "Завершён",
    "Завершён",
    "Завершён",
    "Отменён",
    "В обработке",
]


def random_date(start: date, end: date) -> date:
    """Возвращает случайную дату между start и end включительно."""
    delta_days = (end - start).days
    return start + timedelta(days=random.randint(0, delta_days))


def write_customers() -> dict[int, date]:
    output_path = DATA_DIR / "customers.csv"
    customer_registration_dates: dict[int, date] = {}

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "customer_id",
                "customer_name",
                "city",
                "registration_date",
            ]
        )

        for customer_id in range(1, CUSTOMERS_COUNT + 1):
            registration_date = random_date(
                date(2023, 1, 1),
                date(2026, 6, 30),
            )

            customer_registration_dates[customer_id] = registration_date

            writer.writerow(
                [
                    customer_id,
                    fake.name(),
                    random.choice(CITIES),
                    registration_date.isoformat(),
                ]
            )

    print(f"Создан файл: {output_path}")
    return customer_registration_dates

def write_products() -> list[dict[str, int | float | str]]:
    output_path = DATA_DIR / "products.csv"
    products: list[dict[str, int | float | str]] = []

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        writer.writerow(
            [
                "product_id",
                "product_name",
                "category",
                "purchase_price",
                "sale_price",
            ]
        )

        for product_id in range(1, PRODUCTS_COUNT + 1):
            category = random.choice(list(CATEGORIES))
            base_name = random.choice(CATEGORIES[category])

            purchase_price = round(random.uniform(300, 15_000), 2)
            markup = random.uniform(1.2, 2.1)
            sale_price = round(purchase_price * markup, 2)

            product = {
                "product_id": product_id,
                "product_name": f"{base_name} {product_id}",
                "category": category,
                "purchase_price": purchase_price,
                "sale_price": sale_price,
            }

            products.append(product)

            writer.writerow(
                [
                    product["product_id"],
                    product["product_name"],
                    product["category"],
                    product["purchase_price"],
                    product["sale_price"],
                ]
            )

    print(f"Создан файл: {output_path}")
    return products

def write_orders_and_items(
    products: list[dict[str, int | float | str]],
    customer_registration_dates: dict[int, date],
) -> None:
    orders_path = DATA_DIR / "orders.csv"
    items_path = DATA_DIR / "order_items.csv"

    order_item_id = 1

    with (
        orders_path.open("w", newline="", encoding="utf-8") as orders_file,
        items_path.open("w", newline="", encoding="utf-8") as items_file,
    ):
        orders_writer = csv.writer(orders_file)
        items_writer = csv.writer(items_file)

        orders_writer.writerow(
            [
                "order_id",
                "customer_id",
                "order_date",
                "order_status",
            ]
        )

        items_writer.writerow(
            [
                "order_item_id",
                "order_id",
                "product_id",
                "quantity",
                "unit_price",
            ]
        )

        for order_id in range(1, ORDERS_COUNT + 1):
            customer_id = random.randint(1, CUSTOMERS_COUNT)

            registration_date = customer_registration_dates[customer_id]

            order_date = random_date(
            max(registration_date, date(2024, 1, 1)),
            date(2026, 6, 30),
            )

            order_status = random.choice(ORDER_STATUSES)

            orders_writer.writerow(
                [
                    order_id,
                    customer_id,
                    order_date.isoformat(),
                    order_status,
                ]
            )

            items_count = random.randint(
                MIN_ITEMS_PER_ORDER,
                MAX_ITEMS_PER_ORDER,
            )

            selected_products = random.sample(
                products,
                k=items_count,
            )

            for product in selected_products:
                quantity = random.randint(1, 4)

                base_price = float(product["sale_price"])
                discount = random.choice(
                    [0, 0, 0, 0.05, 0.10, 0.15]
                )

                unit_price = round(
                    base_price * (1 - discount),
                    2,
                )

                items_writer.writerow(
                    [
                        order_item_id,
                        order_id,
                        product["product_id"],
                        quantity,
                        unit_price,
                    ]
                )

                order_item_id += 1

    print(f"Создан файл: {orders_path}")
    print(f"Создан файл: {items_path}")
    print(f"Создано позиций заказа: {order_item_id - 1:,}")


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    print("Начинаем генерацию данных...")

    customer_registration_dates = write_customers()
    products = write_products()

    write_orders_and_items(
    	products,
    	customer_registration_dates,
    )
    print("Генерация завершена.")


if __name__ == "__main__":
    main()