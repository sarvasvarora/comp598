class IDGenerator():
    def __init__(self, init_id: int = 0, prefix: str = None):
        self.id = init_id
        self.prefix = prefix
        def _counter():
            while True:
                yield self.id
                self.id += 1
        self._c = _counter()
    
    def generate_id(self):
        return f"{self.prefix}_{next(self._c)}" if self.prefix else str(next(self._c))