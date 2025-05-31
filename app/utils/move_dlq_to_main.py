import asyncio
from app.amps.rabbit_mq_manager import RabbitMQManager
from app.amps.rabbit_mq_client import RabbitMQClient
from app.config import get_config
from aiormq.abc import ExchangeType

async def move_dlq_to_main(queue_name: str, exchange_name: str):
    # Setup RabbitMQManager
    config = get_config()
    rabbit_client = RabbitMQClient(config.RABBITMQ_URL)
    manager = RabbitMQManager(rabbit_client)
    await manager.setup_exchange(exchange_name, ExchangeType.TOPIC, True)
    await manager.setup_queue_with_retry(queue_name, exchange_name)
    channel = manager.channel

    # Get queue objects
    dlq_name = f"{queue_name}.dlq"
    main_queue = await channel.get_queue(queue_name, ensure=True)
    dlq_queue = await channel.get_queue(dlq_name, ensure=True)

    print(f"Scanning DLQ: {dlq_name} for messages...")

    # Consume all messages from DLQ and republish to main queue
    async with dlq_queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                print(f"Found message in DLQ: {message.body}")
                # Republish to main queue
                await channel.default_exchange.publish(
                    message,
                    routing_key=queue_name
                )
                print(f"Moved message back to main queue: {queue_name}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python move_dlq_to_main.py <queue_name> <exchange_name>")
        sys.exit(1)
    queue_name = sys.argv[1]
    exchange_name = sys.argv[2]
    asyncio.run(move_dlq_to_main(queue_name, exchange_name)) 