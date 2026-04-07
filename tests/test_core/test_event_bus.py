"""Event Bus 测试"""

import asyncio

import pytest
from src.core.event_bus import EventBus, Event, EventType


class TestEventBus:
    @pytest.fixture
    def bus(self):
        return EventBus()

    def _run(self, coro):
        """安全运行异步函数"""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return asyncio.run(coro)

    def test_subscribe_and_publish(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.MESSAGE_CREATED, handler)
        event = Event(type=EventType.MESSAGE_CREATED, data={"msg": "test"})
        self._run(bus.publish(event))

        assert len(received) == 1
        assert received[0].data["msg"] == "test"

    def test_unsubscribe(self, bus):
        received = []

        async def handler(event):
            received.append(event)

        bus.subscribe(EventType.ERROR, handler)
        bus.unsubscribe(EventType.ERROR, handler)

        event = Event(type=EventType.ERROR, data={})
        self._run(bus.publish(event))

        assert len(received) == 0

    def test_multiple_subscribers(self, bus):
        results = []

        async def h1(e):
            results.append("h1")

        async def h2(e):
            results.append("h2")

        bus.subscribe(EventType.AGENT_LOADED, h1)
        bus.subscribe(EventType.AGENT_LOADED, h2)

        self._run(bus.publish(Event(type=EventType.AGENT_LOADED)))

        assert "h1" in results
        assert "h2" in results
