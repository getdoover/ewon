from typing import Any, Callable, Awaitable
import asyncio
from diff import generate_diff, apply_diff
from utils import call_maybe_async
import logging

log = logging.getLogger(__name__)

class TestApp:

    def __init__(self):
        self._tag_values = {}
        self._tag_subscriptions = {}

        self.app_key = "test_app"

    async def set_tag(self, tag_key, value, app_key: str = None, global_tag: bool = False):
        new_values = self._tag_values.copy()
        if global_tag:
            new_values = {tag_key: value}
        else:
            new_values = {app_key or self.app_key: {tag_key: value}}
        new_values = apply_diff(self._tag_values, new_values, do_delete=False)
        if global_tag:
            await self._on_tag_update(None, new_values)
        else:
            await self._on_tag_update(None, new_values)

    async def _on_tag_update(self, _, tag_values: dict[str, Any]):
        diff = generate_diff(self._tag_values, tag_values, do_delete=False)
        self._tag_values = tag_values or {}
        await self.fulfill_tag_subscriptions(diff)

    async def fulfill_tag_subscriptions(self, diff):
        if diff is None or len(diff) == 0:
            return
        
        async def _wrap_callback(callback, tag_key, new_value):
            try:
                await asyncio.wait_for(call_maybe_async(callback, tag_key, new_value), timeout=1)
            except Exception as e:
                log.exception(f"Error in {callback.__name__}: {e}", exc_info=e)

        for k, callback in self._tag_subscriptions.items():
            if isinstance(k, tuple):
                app_key, tag_key = k
                if app_key in diff and tag_key in diff[app_key]:
                    new_value = self._tag_values[app_key][tag_key] if app_key in self._tag_values and tag_key in self._tag_values[app_key] else None
                    await _wrap_callback(callback, tag_key, new_value)
            else:
                if k in diff:
                    new_value = self._tag_values[k] if k in self._tag_values else None
                    await _wrap_callback(callback, k, new_value)

    def subscribe_to_tag(self,
                        tag_key: str,
                        callback: Callable[[str, dict[str, Any]], Awaitable[Any]] | Callable[[str, dict[str, Any]], Any],
                        app_key: str = None, global_tag: bool = False, 
                    ):
        if global_tag:
            self._tag_subscriptions[tag_key] = callback
        else:
            self._tag_subscriptions[(app_key, tag_key)] = callback


async def main():
    app = TestApp()
    app.subscribe_to_tag("test_tag2", app_key="test_app", callback=lambda tag_key, tag_value: print(f"test_tag: {tag_key} = {tag_value}"))
    app.subscribe_to_tag("global", global_tag=True, callback=lambda tag_key, tag_value: print(f"global: {tag_key} = {tag_value}"))
    

    print(app._tag_subscriptions)
    await app.set_tag("test_tag", "test_value")
    await app.set_tag("test_tag", "test_value")
    await app.set_tag("test_tag", "test_value2")
    await app.set_tag("test_tag2", "yeeha")
    await app.set_tag("test_tag2", "yeeha")
    await app.set_tag("test_tag2", 4)
    await app.set_tag("test_tag2", None)
    await app.set_tag("test_tag2", None)
    await app.set_tag("test_tag2", {"test": "testValue"})
    await app.set_tag("test_tag2", {"test": "testValue2"})
    await app.set_tag("test_tag2", {"test": "testValue2"})

    await app.set_tag("global", "global_value", global_tag=True)
    await app.set_tag("global", "global_value", global_tag=True)
    await app.set_tag("global", "global_value2", global_tag=True)

    print(app._tag_values)

if __name__ == "__main__":
    asyncio.run(main())