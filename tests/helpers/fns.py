import asyncio
import itertools
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


def base_permutations[T, U](group: t.Iterable[T], value: U) -> dict[tuple[T, ...], U]:
    """
    helper to generate a background set of permuted indexes which can be selectively updated.

    this simplifies the process of fully covering a range of possible inputs.  for example,
    if a truth table of 3 inputs is:
        0 1 2 |
        ------+-----
        0 0 0 | ERR
        0 0 1 | ERR
        0 1 0 | ERR
        0 1 1 | ERR
        1 0 0 | "yellow"
        1 0 1 | ERR
        1 1 0 | "green"
        1 1 1 | ERR

    instead of writing the full table, we can focus on the non-default cases:

    permutations = base_permutations([0,1,2], ValueError)
    permutations.update({
        (0,): "yellow",
        (0, 1): "green"
    })
    verify(permutations, args)
    """
    res = {}
    group = list(group)
    for r in range(len(group) + 1):
        for c in itertools.combinations(group, r):
            res[c] = value
    return res
