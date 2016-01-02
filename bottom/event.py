import asyncio


class EventsMixin(object):
    def __init__(self, *, loop):
        self._handlers = {}
        self.loop = loop

    def _add_event(self, event, func):
        '''
        Validate the func's signature, then partial_bind the function to speed
        up argument injection.

        '''
        if not asyncio.iscoroutinefunction(func):
            func = asyncio.coroutine(func)
        if event not in self._handlers:
            self._handlers[event] = list()
        self._handlers[event].append(func)
        return func

    def trigger(self, event, **kwargs):
        for func in self._handlers.get(event, []):
            self.loop.create_task(func(**kwargs))

    def on(self, event):
        '''
        Decorate a function to be invoked when the given :param:`event` occurs.
        The function may be a coroutine.

        Returns
        -------
        A decorator that takes a function and registers it with the event.

        Example
        -------
        import asyncio

        events = EventsMixin({'test': ['arg', 'one', 'two']})

        @events.on('test')
        def func(one, arg):
            print(arg, one)

        event = 'test'
        kwargs = {'one': 1, 'two': 2, 'arg': 'arg'}

        events.trigger(event, **kwargs)
        loop = asyncio.get_event_loop()
        # Run all queued events
        loop.stop()
        loop.run_forever()

        '''
        def wrap_function(func):
            self._add_event(event, func)
            return func
        return wrap_function
