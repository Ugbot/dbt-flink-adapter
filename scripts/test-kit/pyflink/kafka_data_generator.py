"""
Kafka data generator for Flink testing.

Generates realistic user behavior events using Faker and publishes to Kafka.
Demonstrates real data generation following the project philosophy:
- No hardcoded test data
- Use Faker for realistic values
- Randomized, unique data
- Production-quality code

Requirements:
- kafka-python>=2.0.0
- faker>=20.0.0
- Python 3.13+
"""

import json
import logging
import time
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from kafka import KafkaProducer
    from kafka.errors import KafkaError
except ImportError:
    raise ImportError(
        "kafka-python not installed. Run: pip install kafka-python"
    )

try:
    from faker import Faker
except ImportError:
    raise ImportError(
        "faker not installed. Run: pip install faker"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """User behavior event types."""
    PAGE_VIEW = "page_view"
    CLICK = "click"
    ADD_TO_CART = "add_to_cart"
    REMOVE_FROM_CART = "remove_from_cart"
    PURCHASE = "purchase"
    SEARCH = "search"
    LOGIN = "login"
    LOGOUT = "logout"
    SIGNUP = "signup"
    REVIEW = "review"


@dataclass
class UserEvent:
    """User behavior event data class."""
    event_id: str
    user_id: str
    session_id: str
    event_type: str
    timestamp: str
    ip_address: str
    user_agent: str
    country: str
    city: str
    device_type: str
    page_url: Optional[str] = None
    product_id: Optional[str] = None
    product_name: Optional[str] = None
    product_category: Optional[str] = None
    product_price: Optional[float] = None
    quantity: Optional[int] = None
    search_query: Optional[str] = None
    rating: Optional[int] = None


class EventGenerator:
    """Generates realistic user behavior events using Faker."""

    def __init__(self, seed: Optional[int] = None) -> None:
        """
        Initialize event generator.

        Args:
            seed: Random seed for reproducibility (optional)
        """
        self.faker = Faker()
        if seed is not None:
            Faker.seed(seed)

        logger.info("Event generator initialized")

    def generate_user_event(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        event_type: Optional[EventType] = None
    ) -> UserEvent:
        """
        Generate a realistic user behavior event.

        Args:
            user_id: Optional specific user ID, otherwise random UUID
            session_id: Optional specific session ID, otherwise random UUID
            event_type: Optional specific event type, otherwise random

        Returns:
            UserEvent instance with realistic data
        """
        if user_id is None:
            user_id = str(uuid.uuid4())

        if session_id is None:
            session_id = str(uuid.uuid4())

        if event_type is None:
            event_type = self.faker.random_element(list(EventType))

        event = UserEvent(
            event_id=str(uuid.uuid4()),
            user_id=user_id,
            session_id=session_id,
            event_type=event_type.value,
            timestamp=datetime.utcnow().isoformat(),
            ip_address=self.faker.ipv4(),
            user_agent=self.faker.user_agent(),
            country=self.faker.country_code(),
            city=self.faker.city(),
            device_type=self.faker.random_element([
                "desktop", "mobile", "tablet"
            ])
        )

        # Add event-specific fields
        if event_type in [
            EventType.PAGE_VIEW,
            EventType.CLICK,
            EventType.ADD_TO_CART,
            EventType.REMOVE_FROM_CART,
            EventType.PURCHASE
        ]:
            event.page_url = self.faker.url()
            event.product_id = str(uuid.uuid4())
            event.product_name = self.faker.catch_phrase()
            event.product_category = self.faker.random_element([
                "Electronics", "Clothing", "Books", "Home & Garden",
                "Sports", "Toys", "Food & Beverage", "Beauty"
            ])
            event.product_price = round(
                float(self.faker.random_int(min=10, max=1000)) +
                self.faker.random.random(),
                2
            )

            if event_type in [
                EventType.ADD_TO_CART,
                EventType.REMOVE_FROM_CART,
                EventType.PURCHASE
            ]:
                event.quantity = self.faker.random_int(min=1, max=5)

        elif event_type == EventType.SEARCH:
            event.search_query = " ".join(self.faker.words(nb=3))

        elif event_type == EventType.REVIEW:
            event.product_id = str(uuid.uuid4())
            event.product_name = self.faker.catch_phrase()
            event.rating = self.faker.random_int(min=1, max=5)

        return event

    def generate_event_batch(
        self,
        batch_size: int,
        user_pool_size: int = 1000,
        session_length: int = 10
    ) -> List[UserEvent]:
        """
        Generate a batch of related events simulating realistic user behavior.

        Args:
            batch_size: Number of events to generate
            user_pool_size: Size of user pool to simulate
            session_length: Average number of events per session

        Returns:
            List of UserEvent instances
        """
        events: List[UserEvent] = []

        # Generate pool of user IDs
        user_ids = [str(uuid.uuid4()) for _ in range(user_pool_size)]

        # Track active sessions
        active_sessions: Dict[str, str] = {}

        for _ in range(batch_size):
            # Pick random user
            user_id = self.faker.random_element(user_ids)

            # Get or create session for user
            if user_id in active_sessions:
                session_id = active_sessions[user_id]
            else:
                session_id = str(uuid.uuid4())
                active_sessions[user_id] = session_id

            # Generate event
            event = self.generate_user_event(
                user_id=user_id,
                session_id=session_id
            )
            events.append(event)

            # Randomly end sessions
            if self.faker.random_int(min=1, max=session_length) == 1:
                if user_id in active_sessions:
                    del active_sessions[user_id]

        return events


class KafkaEventProducer:
    """Publishes events to Kafka."""

    def __init__(
        self,
        bootstrap_servers: str = "localhost:9092",
        topic: str = "user_events"
    ) -> None:
        """
        Initialize Kafka producer.

        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Kafka topic to publish to
        """
        self.topic = topic
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
            max_in_flight_requests_per_connection=1
        )
        logger.info(f"Kafka producer initialized for topic: {topic}")

    def send_event(self, event: UserEvent) -> None:
        """
        Send single event to Kafka.

        Args:
            event: UserEvent to publish
        """
        try:
            future = self.producer.send(
                self.topic,
                key=event.user_id,
                value=asdict(event)
            )

            # Wait for send to complete
            record_metadata = future.get(timeout=10)
            logger.debug(
                f"Event sent: topic={record_metadata.topic}, "
                f"partition={record_metadata.partition}, "
                f"offset={record_metadata.offset}"
            )

        except KafkaError as e:
            logger.error(f"Failed to send event: {e}")
            raise

    def send_batch(self, events: List[UserEvent]) -> None:
        """
        Send batch of events to Kafka.

        Args:
            events: List of UserEvents to publish
        """
        for event in events:
            self.send_event(event)

        # Flush to ensure all messages are sent
        self.producer.flush()
        logger.info(f"Sent batch of {len(events)} events")

    def close(self) -> None:
        """Close Kafka producer."""
        self.producer.close()
        logger.info("Kafka producer closed")


def run_continuous_generator(
    kafka_servers: str = "localhost:9092",
    topic: str = "user_events",
    events_per_second: int = 10,
    user_pool_size: int = 1000,
    duration_seconds: Optional[int] = None
) -> None:
    """
    Run continuous event generation to Kafka.

    Args:
        kafka_servers: Kafka broker addresses
        topic: Kafka topic
        events_per_second: Target rate of event generation
        user_pool_size: Number of unique users to simulate
        duration_seconds: Run duration (None for infinite)
    """
    logger.info("=" * 80)
    logger.info("Starting Continuous Event Generator")
    logger.info("=" * 80)
    logger.info(f"Kafka servers: {kafka_servers}")
    logger.info(f"Topic: {topic}")
    logger.info(f"Target rate: {events_per_second} events/second")
    logger.info(f"User pool size: {user_pool_size}")
    logger.info("=" * 80)

    generator = EventGenerator()
    producer = KafkaEventProducer(
        bootstrap_servers=kafka_servers,
        topic=topic
    )

    start_time = time.time()
    total_events = 0

    try:
        while True:
            batch_start = time.time()

            # Generate and send events
            events = generator.generate_event_batch(
                batch_size=events_per_second,
                user_pool_size=user_pool_size
            )
            producer.send_batch(events)

            total_events += len(events)
            elapsed = time.time() - start_time

            # Log progress every 10 seconds
            if int(elapsed) % 10 == 0 and int(elapsed) > 0:
                rate = total_events / elapsed
                logger.info(
                    f"Progress: {total_events} events sent, "
                    f"avg rate: {rate:.2f} events/sec"
                )

            # Check duration limit
            if duration_seconds and elapsed >= duration_seconds:
                logger.info(f"Duration limit reached: {duration_seconds} seconds")
                break

            # Sleep to maintain target rate
            batch_duration = time.time() - batch_start
            sleep_time = max(0, 1.0 - batch_duration)
            time.sleep(sleep_time)

    except KeyboardInterrupt:
        logger.info("Generator stopped by user")
    finally:
        producer.close()
        elapsed = time.time() - start_time
        avg_rate = total_events / elapsed if elapsed > 0 else 0
        logger.info(f"Total events sent: {total_events}")
        logger.info(f"Average rate: {avg_rate:.2f} events/second")
        logger.info(f"Total duration: {elapsed:.2f} seconds")


def generate_sample_batch(count: int = 10) -> None:
    """
    Generate and print sample events for testing.

    Args:
        count: Number of sample events to generate
    """
    logger.info(f"Generating {count} sample events:")
    logger.info("=" * 80)

    generator = EventGenerator(seed=42)  # Use seed for reproducibility
    events = generator.generate_event_batch(batch_size=count)

    for i, event in enumerate(events, 1):
        logger.info(f"\nEvent {i}:")
        logger.info(json.dumps(asdict(event), indent=2))


def main() -> None:
    """Main entry point."""
    import sys
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate realistic user events to Kafka"
    )
    parser.add_argument(
        "--kafka-servers",
        default="localhost:9092",
        help="Kafka bootstrap servers (default: localhost:9092)"
    )
    parser.add_argument(
        "--topic",
        default="user_events",
        help="Kafka topic (default: user_events)"
    )
    parser.add_argument(
        "--rate",
        type=int,
        default=10,
        help="Events per second (default: 10)"
    )
    parser.add_argument(
        "--users",
        type=int,
        default=1000,
        help="User pool size (default: 1000)"
    )
    parser.add_argument(
        "--duration",
        type=int,
        help="Duration in seconds (default: infinite)"
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Generate sample events and exit (no Kafka needed)"
    )

    args = parser.parse_args()

    if args.sample:
        generate_sample_batch(count=10)
    else:
        run_continuous_generator(
            kafka_servers=args.kafka_servers,
            topic=args.topic,
            events_per_second=args.rate,
            user_pool_size=args.users,
            duration_seconds=args.duration
        )


if __name__ == "__main__":
    main()
