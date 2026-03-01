#!/usr/bin/env python3
"""
Continuous data generator for the MongoDB → Flink → Kafka → PG demo.

Generates realistic e-commerce data (customers, products, orders) and
continuously inserts/updates documents in MongoDB. The Flink CDC pipeline
picks up these changes via MongoDB change streams.

Usage:
    python generate.py                          # 5 ops/sec, runs forever
    python generate.py --rate 10                # 10 ops/sec
    python generate.py --rate 5 --duration 120  # 5 ops/sec for 2 minutes
    python generate.py --seed-only              # Just seed initial data, then exit
"""

import argparse
import logging
import random
import signal
import sys
import time
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from faker import Faker
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, OperationFailure

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

fake = Faker()

# Product catalog categories and realistic names
CATEGORIES = {
    "Electronics": [
        "Wireless Headphones", "USB-C Hub", "Portable Charger", "Bluetooth Speaker",
        "Webcam HD", "Mechanical Keyboard", "Gaming Mouse", "Monitor Stand",
        "Lightning Cable", "Smart Watch", "Tablet Stand", "External SSD",
    ],
    "Clothing": [
        "Cotton T-Shirt", "Denim Jeans", "Wool Sweater", "Running Shoes",
        "Baseball Cap", "Leather Belt", "Silk Scarf", "Rain Jacket",
        "Hiking Boots", "Sport Socks", "Polo Shirt", "Cargo Shorts",
    ],
    "Home & Kitchen": [
        "Coffee Maker", "Blender", "Cutting Board", "Knife Set",
        "Cast Iron Pan", "Water Bottle", "Tea Kettle", "Toaster",
        "Mixing Bowls", "Spice Rack", "Dish Towels", "Food Container",
    ],
    "Books": [
        "Python Cookbook", "Data Engineering", "Clean Code", "System Design",
        "Machine Learning", "SQL Performance", "Kafka Definitive Guide",
        "Streaming Systems", "Designing Data Apps", "The Art of SQL",
        "Database Internals", "Flink in Action",
    ],
}

ORDER_STATUSES = ["pending", "confirmed", "shipped", "delivered", "cancelled"]
STATUS_TRANSITIONS = {
    "pending": "confirmed",
    "confirmed": "shipped",
    "shipped": "delivered",
}

# Operation weights: what percentage of operations are each type
OP_WEIGHTS = {
    "new_order": 55,
    "update_order_status": 20,
    "new_customer": 15,
    "update_stock": 10,
}


class DataGenerator:
    """Generates and manages e-commerce data in MongoDB."""

    def __init__(self, mongo_uri: str = "mongodb://localhost:27117/?directConnection=true"):
        self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
        self.db = self.client["ecommerce"]
        self.customers = self.db["customers"]
        self.products = self.db["products"]
        self.orders = self.db["orders"]

        self._customer_ids: List[str] = []
        self._product_ids: List[str] = []
        self._pending_order_ids: List[str] = []

        self.stats = {
            "customers_created": 0,
            "products_created": 0,
            "orders_created": 0,
            "orders_updated": 0,
            "stock_updated": 0,
        }

    def verify_connection(self) -> None:
        """Verify MongoDB is reachable and is a replica set."""
        try:
            self.client.admin.command("ping")
        except ConnectionFailure as e:
            logger.error("Cannot connect to MongoDB: %s", e)
            raise

        try:
            status = self.client.admin.command("replSetGetStatus")
            primary_count = sum(
                1 for m in status.get("members", []) if m.get("stateStr") == "PRIMARY"
            )
            if primary_count == 0:
                raise OperationFailure("No PRIMARY member in replica set")
            logger.info(
                "Connected to MongoDB replica set '%s' with %d member(s)",
                status.get("set"),
                len(status.get("members", [])),
            )
        except OperationFailure as e:
            logger.error("MongoDB is not a replica set (required for CDC): %s", e)
            raise

    def seed_products(self) -> None:
        """Seed the product catalog if empty."""
        if self.products.count_documents({}) > 0:
            logger.info("Products collection already seeded, loading existing IDs")
            self._product_ids = [
                doc["product_id"] for doc in self.products.find({}, {"product_id": 1})
            ]
            return

        docs = []
        for category, names in CATEGORIES.items():
            for name in names:
                product_id = str(uuid.uuid4())[:12]
                docs.append(
                    {
                        "product_id": product_id,
                        "name": name,
                        "category": category,
                        "price": float(round(random.uniform(5.99, 299.99), 2)),
                        "stock": random.randint(10, 500),
                    }
                )
                self._product_ids.append(product_id)

        self.products.insert_many(docs)
        self.stats["products_created"] = len(docs)
        logger.info("Seeded %d products across %d categories", len(docs), len(CATEGORIES))

    def seed_customers(self, count: int = 50) -> None:
        """Seed initial customers if collection is empty."""
        if self.customers.count_documents({}) > 0:
            logger.info("Customers collection already seeded, loading existing IDs")
            self._customer_ids = [
                doc["customer_id"]
                for doc in self.customers.find({}, {"customer_id": 1})
            ]
            return

        docs = []
        for _ in range(count):
            customer_id = str(uuid.uuid4())[:12]
            docs.append(
                {
                    "customer_id": customer_id,
                    "name": fake.name(),
                    "email": fake.email(),
                    "city": fake.city(),
                    "created_at": datetime.now(timezone.utc),
                }
            )
            self._customer_ids.append(customer_id)

        self.customers.insert_many(docs)
        self.stats["customers_created"] = count
        logger.info("Seeded %d customers", count)

    def seed_orders(self, count: int = 20) -> None:
        """Seed initial orders if collection is empty."""
        if self.orders.count_documents({}) > 0:
            logger.info("Orders collection already seeded, loading existing IDs")
            pending = self.orders.find(
                {"status": {"$in": ["pending", "confirmed", "shipped"]}},
                {"order_id": 1},
            )
            self._pending_order_ids = [doc["order_id"] for doc in pending]
            return

        if not self._customer_ids or not self._product_ids:
            logger.warning("Cannot seed orders: no customers or products")
            return

        docs = []
        for _ in range(count):
            order_id = str(uuid.uuid4())[:12]
            product = self.products.find_one(
                {"product_id": random.choice(self._product_ids)}
            )
            quantity = random.randint(1, 5)
            price = product["price"] if product else 19.99
            now = datetime.now(timezone.utc)
            status = random.choice(["pending", "confirmed"])
            docs.append(
                {
                    "order_id": order_id,
                    "customer_id": random.choice(self._customer_ids),
                    "product_id": product["product_id"] if product else "unknown",
                    "quantity": quantity,
                    "total": float(round(price * quantity, 2)),
                    "status": status,
                    "created_at": now,
                    "updated_at": now,
                }
            )
            if status in STATUS_TRANSITIONS:
                self._pending_order_ids.append(order_id)

        self.orders.insert_many(docs)
        self.stats["orders_created"] = count
        logger.info("Seeded %d initial orders", count)

    def create_customer(self) -> None:
        """Insert a new customer."""
        customer_id = str(uuid.uuid4())[:12]
        doc = {
            "customer_id": customer_id,
            "name": fake.name(),
            "email": fake.email(),
            "city": fake.city(),
            "created_at": datetime.now(timezone.utc),
        }
        self.customers.insert_one(doc)
        self._customer_ids.append(customer_id)
        self.stats["customers_created"] += 1
        logger.debug("Created customer %s (%s)", customer_id, doc["name"])

    def create_order(self) -> None:
        """Insert a new order for a random customer and product."""
        if not self._customer_ids or not self._product_ids:
            return

        order_id = str(uuid.uuid4())[:12]
        product = self.products.find_one(
            {"product_id": random.choice(self._product_ids)}
        )
        if not product:
            return

        quantity = random.randint(1, 5)
        now = datetime.now(timezone.utc)
        doc = {
            "order_id": order_id,
            "customer_id": random.choice(self._customer_ids),
            "product_id": product["product_id"],
            "quantity": quantity,
            "total": float(round(product["price"] * quantity, 2)),
            "status": "pending",
            "created_at": now,
            "updated_at": now,
        }
        self.orders.insert_one(doc)
        self._pending_order_ids.append(order_id)
        self.stats["orders_created"] += 1
        logger.debug(
            "Created order %s: %dx %s ($%.2f)",
            order_id,
            quantity,
            product["name"],
            doc["total"],
        )

    def update_order_status(self) -> None:
        """Advance a random pending/confirmed/shipped order to the next status."""
        if not self._pending_order_ids:
            return

        order_id = random.choice(self._pending_order_ids)
        order = self.orders.find_one({"order_id": order_id})
        if not order:
            self._pending_order_ids.remove(order_id)
            return

        current_status = order["status"]
        next_status = STATUS_TRANSITIONS.get(current_status)
        if not next_status:
            self._pending_order_ids.remove(order_id)
            return

        self.orders.update_one(
            {"order_id": order_id},
            {
                "$set": {
                    "status": next_status,
                    "updated_at": datetime.now(timezone.utc),
                }
            },
        )
        self.stats["orders_updated"] += 1
        logger.debug(
            "Order %s: %s → %s", order_id, current_status, next_status
        )

        # Remove from pending list if terminal state
        if next_status not in STATUS_TRANSITIONS:
            self._pending_order_ids.remove(order_id)

    def update_stock(self) -> None:
        """Randomly adjust stock for a product."""
        if not self._product_ids:
            return

        product_id = random.choice(self._product_ids)
        adjustment = random.randint(-10, 50)
        self.products.update_one(
            {"product_id": product_id},
            {"$inc": {"stock": adjustment}},
        )
        self.stats["stock_updated"] += 1
        logger.debug("Product %s stock adjusted by %+d", product_id, adjustment)

    def pick_operation(self) -> str:
        """Choose a random operation based on weights."""
        ops = list(OP_WEIGHTS.keys())
        weights = list(OP_WEIGHTS.values())
        return random.choices(ops, weights=weights, k=1)[0]

    def execute_operation(self) -> None:
        """Execute a single random operation."""
        op = self.pick_operation()
        if op == "new_order":
            self.create_order()
        elif op == "update_order_status":
            self.update_order_status()
        elif op == "new_customer":
            self.create_customer()
        elif op == "update_stock":
            self.update_stock()

    def print_stats(self) -> None:
        """Print current statistics."""
        logger.info(
            "Stats: customers=%d orders=%d (updated=%d) stock_updates=%d",
            self.stats["customers_created"],
            self.stats["orders_created"],
            self.stats["orders_updated"],
            self.stats["stock_updated"],
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate e-commerce data into MongoDB for Flink CDC demo"
    )
    parser.add_argument(
        "--mongo-uri",
        default="mongodb://localhost:27117/?directConnection=true",
        help="MongoDB connection URI (default: mongodb://localhost:27117/?directConnection=true)",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=5.0,
        help="Operations per second (default: 5)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=0,
        help="Duration in seconds, 0 = run forever (default: 0)",
    )
    parser.add_argument(
        "--seed-only",
        action="store_true",
        help="Only seed initial data, then exit",
    )
    parser.add_argument(
        "--seed-customers",
        type=int,
        default=50,
        help="Number of initial customers to seed (default: 50)",
    )
    parser.add_argument(
        "--seed-orders",
        type=int,
        default=20,
        help="Number of initial orders to seed (default: 20)",
    )
    args = parser.parse_args()

    gen = DataGenerator(mongo_uri=args.mongo_uri)

    logger.info("Connecting to MongoDB at %s", args.mongo_uri)
    gen.verify_connection()

    logger.info("Seeding initial data...")
    gen.seed_products()
    gen.seed_customers(count=args.seed_customers)
    gen.seed_orders(count=args.seed_orders)
    gen.print_stats()

    if args.seed_only:
        logger.info("Seed complete. Exiting (--seed-only mode).")
        return

    # Graceful shutdown on Ctrl+C
    shutdown = False

    def signal_handler(sig: int, frame: Optional[object]) -> None:
        nonlocal shutdown
        shutdown = True
        logger.info("Shutting down...")

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    interval = 1.0 / args.rate
    start_time = time.time()
    ops_count = 0
    last_stats_time = start_time

    logger.info(
        "Starting continuous generation at %.1f ops/sec%s",
        args.rate,
        f" for {args.duration}s" if args.duration > 0 else " (Ctrl+C to stop)",
    )

    while not shutdown:
        if args.duration > 0 and (time.time() - start_time) >= args.duration:
            logger.info("Duration reached (%ds). Stopping.", args.duration)
            break

        gen.execute_operation()
        ops_count += 1

        # Print stats every 30 seconds
        now = time.time()
        if now - last_stats_time >= 30:
            elapsed = now - start_time
            actual_rate = ops_count / elapsed if elapsed > 0 else 0
            logger.info(
                "Progress: %d ops in %.0fs (%.1f ops/sec actual)",
                ops_count,
                elapsed,
                actual_rate,
            )
            gen.print_stats()
            last_stats_time = now

        time.sleep(interval)

    gen.print_stats()
    logger.info("Done. Total operations: %d", ops_count)


if __name__ == "__main__":
    main()
