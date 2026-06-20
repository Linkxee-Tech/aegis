import pytest

from backend.orchestrator.message_bus import MessageBus


@pytest.mark.asyncio
async def test_publish_with_no_subscribers_does_not_raise(message_bus: MessageBus):
    await message_bus.publish("nobody.listening", {"foo": "bar"})


@pytest.mark.asyncio
async def test_subscriber_receives_published_message(message_bus: MessageBus):
    received = []

    async def handler(message: dict) -> None:
        received.append(message)

    message_bus.subscribe("topic.a", handler)
    await message_bus.publish("topic.a", {"value": 1})

    assert received == [{"value": 1}]


@pytest.mark.asyncio
async def test_unsubscribe_stops_further_delivery(message_bus: MessageBus):
    received = []

    async def handler(message: dict) -> None:
        received.append(message)

    message_bus.subscribe("topic.b", handler)
    message_bus.unsubscribe("topic.b", handler)
    await message_bus.publish("topic.b", {"value": 1})

    assert received == []


@pytest.mark.asyncio
async def test_one_failing_handler_does_not_block_others(message_bus: MessageBus):
    received = []

    async def failing_handler(message: dict) -> None:
        raise RuntimeError("boom")

    async def good_handler(message: dict) -> None:
        received.append(message)

    message_bus.subscribe("topic.c", failing_handler)
    message_bus.subscribe("topic.c", good_handler)
    await message_bus.publish("topic.c", {"value": 42})

    assert received == [{"value": 42}]
