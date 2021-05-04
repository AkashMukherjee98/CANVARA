def register(registry, operation_name):
    """Accumulate operation name to function mapping"""
    def _register(func):
        registry[operation_name] = func
        return func
    return _register
