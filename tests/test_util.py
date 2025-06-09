import asyncio
import gc

from bottom import util


async def test_create_task():
    """tasks complete even if the only caller-managed referece is gc'd"""
    called = asyncio.Event()

    async def call():
        called.set()

    task = util.create_task(call())
    # NOTE: if you debug this test and set a breakpoint before counting refs,
    # then your debugger may grab an additional ref to the task and fail the check below.
    refs = len(gc.get_referrers(task))
    del task
    gc.collect()
    await called.wait()
    assert refs == 2


async def test_join_empty_tasks():
    """joining empty tasks returns an empty list, but must still be awaited"""
    task = util.join_tasks([])
    assert not task.done()
    assert await task == []


async def test_join_tasks():
    """join_tasks will wait for all tasks to complete, even if one raises"""
    has_raised = asyncio.Event()
    to_raise = ValueError("foobar")

    async def raises():
        has_raised.set()
        raise to_raise

    async def returns():
        await has_raised.wait()
        return 3

    tasks = [asyncio.create_task(coro) for coro in (raises(), returns())]
    exc, value = await util.join_tasks(tasks)
    assert exc is to_raise
    assert value == 3


async def test_ensure_async_self():
    """ensure_async_fn returns the fn without wrapping if it's already async"""

    async def original():
        await asyncio.sleep(2)

    wrapped = util.ensure_async_fn(original)
    assert wrapped is original


async def test_ensure_async_sync():
    """ensure_async_fn returns a wrapper for non-async fns"""
    invoked = False

    def original():
        nonlocal invoked
        invoked = True

    wrapped = util.ensure_async_fn(original)
    assert wrapped is not original

    coro = wrapped()
    assert asyncio.iscoroutine(coro)
    assert not invoked

    # even though the original is sync, the wrapper doesn't immediately invoke it
    await coro
    assert invoked


async def test_stack_process():
    """each processor in a stack is free to call the next handler, or not; and to change args, or not."""
    calls = []

    async def first(next_handler, message):
        calls.append(("first", message))
        await next_handler(message[::-1])

    async def second(next_handler, message):
        calls.append(("second", message))
        await next_handler(message)

    async def third(next_handler, message):
        await next_handler(message[::-1] * 2)
        calls.append(("third", message))

    async def fourth(next_handler, message):
        calls.append(("fourth", "hardcoded"))

    async def not_called(next_handler, message):
        calls.append(("not_called", message))
        await next_handler(message)

    stack = [first, second, third, fourth, not_called]
    task = util.stack_process(stack, "123")
    await task

    expected = [
        ("first", "123"),
        ("second", "321"),
        # third calls the next handler _before_ itself
        ("fourth", "hardcoded"),
        ("third", "321"),
    ]
    assert calls == expected


async def test_process_empty_stack():
    """even though the stack is empty, the return value is still an awaitable task"""
    task = util.stack_process([])  # type: ignore  (type checkers don't like not knowing the ParamSpec)
    assert not task.done()
    result = await task
    assert result is None
