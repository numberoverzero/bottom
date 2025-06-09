import asyncio
import collections
import functools
import typing as t

__all__ = ["create_task"]

__background_tasks__: set[asyncio.Task] = set()


def create_task[T](x: t.Coroutine[t.Any, t.Any, T]) -> asyncio.Task[T]:
    """
    functionally identical to `asyncio.create_task`

    ensures that a reference to the task is kept around until it's done, even
    if the caller doesn't store a reference.  prevents gc from unexpectedly
    reaping the task.

    see also:

    * https://textual.textualize.io/blog/2023/02/11/the-heisenbug-lurking-in-your-async-code/
    * https://docs.astral.sh/ruff/rules/asyncio-dangling-task/
    """
    task = asyncio.create_task(x)
    __background_tasks__.add(task)
    task.add_done_callback(__background_tasks__.discard)
    return task


def join_tasks(tasks: t.Iterable[asyncio.Task]) -> asyncio.Task:
    async def gather() -> None:
        if not tasks:
            return
        await asyncio.gather(*tasks, return_exceptions=True)

    return asyncio.create_task(gather())


def ensure_async_fn[**P, R](
    fn: t.Callable[P, R],
) -> t.Callable[P, t.Coroutine[t.Any, t.Any, R]]:
    """returns the input fn if it was async, otherwise returns an async wrapper around the input fn"""
    if asyncio.iscoroutinefunction(fn):
        return fn
    else:

        @functools.wraps(fn)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            return fn(*args, **kwargs)

        return wrapper


type NextProcessor[**P] = t.Callable[P, t.Coroutine[t.Any, t.Any, t.Any]]
type Processor[**P] = t.Callable[t.Concatenate[NextProcessor[P], P], t.Coroutine[t.Any, t.Any, t.Any]]


def stack_process[**P](fns: t.Iterable[Processor[P]], *args: P.args, **kwargs: P.kwargs) -> asyncio.Task:
    """
    Nested processing from a stack of processors.

    This allows earlier processors to conditionally defer to later
    processors, or to exit early.

    * for a list of processors: `p0, p1, p2`
    * and arguments: `*args, **kwargs`
    * then `stack_process([p0, p1, p2], *args, **kwargs)` will invoke:
    ```
    p0(next, *args, **kwargs)
        -> p1(next, *args, **kwargs)
            -> p2(next, *args, **kwargs)
                -> [no-op]
    ```

    a sample processor could be:
    ```
    async def process(next_processor, *a, *kw):
        if kw.get("fast-exit", False):
            print("short circuiting and bypassing later processors")
        else:
            await next_processor(*a, **kw)
    ```

    note that each processor can modify or replace args:
    ```
    async def sanitize(next_processor, *a, **kw):
        hardcoded_args = ["foo", "bar"]
        for key in ["password", "api_key", "credential"]:
            kw.pop("password", None)
        await next_processor(hardcoded_args, **kw)
    ```
    """
    handlers = collections.deque(fns)

    async def next_processor(*a: P.args, **kw: P.kwargs) -> None:
        if not handlers:
            return
        next = handlers.popleft()
        await next(next_processor, *a, **kw)

    return create_task(next_processor(*args, **kwargs))


type Decorator[**P, R] = t.Callable[[t.Callable[P, R]], t.Callable[P, R]]
