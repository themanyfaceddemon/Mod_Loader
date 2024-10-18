import asyncio
import inspect

import dearpygui.dearpygui as dpg


class Timer:
    __slots__ = [
        "interval",
        "_callback",
        "repeat_count",
        "args",
        "kwargs",
        "_is_coroutine",
        "_task",
        "_running",
    ]

    def __init__(self, interval, callback, repeat_count=None, *args, **kwargs):
        self.interval = interval
        self._callback = callback
        self.repeat_count = repeat_count
        self.args = args
        self.kwargs = kwargs
        self._is_coroutine = inspect.iscoroutinefunction(callback)
        self._task = None
        self._running = False

    async def _run_forever(self):
        while dpg.is_dearpygui_running() and self._running:
            await asyncio.sleep(self.interval)
            if self._is_coroutine:
                await self._callback(*self.args, **self.kwargs)

            else:
                self._callback(*self.args, **self.kwargs)

    async def _run_limited(self):
        counter = 0
        while dpg.is_dearpygui_running() and (
            self.repeat_count is None or counter < self.repeat_count
        ):
            await asyncio.sleep(self.interval)
            if not self._running:
                break

            if self._is_coroutine:
                await self._callback(*self.args, **self.kwargs)
            else:
                self._callback(*self.args, **self.kwargs)

            counter += 1

    def start(self):
        if not self._running:
            self._running = True
            if self.repeat_count is None:
                self._task = asyncio.create_task(self._run_forever())

            else:
                self._task = asyncio.create_task(self._run_limited())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()

    def is_running(self):
        return self._running
