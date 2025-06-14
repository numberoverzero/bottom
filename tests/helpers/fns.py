import asyncio
import time
import typing as t


async def busy_wait(criteria: t.Callable[[], t.Any], timeout_ms: int = 200) -> None:
    """
    helper function to yield execution to other coros without adding a long sleep.

    if the criteria isn't met within the timeout, we assume it was never going to complete.
    this prevents deadlocks from holding the test suite hostage.

    usage"
    ```

    async def test_something():
        asyncio.create_task(setup())
        asyncio.create_task(more_work())

        await busy_wait(lambda: some_struct.count >= 10)

        assert some_struct.values == expected
    ```
    """
    start = time.monotonic_ns()
    while not bool(criteria()):
        await asyncio.sleep(0)
        elapsed = (time.monotonic_ns() - start) / 1_000_000  # ns -> ms
        if elapsed >= timeout_ms:
            raise RuntimeError(f"failed to meet criteria within {max}ms")
