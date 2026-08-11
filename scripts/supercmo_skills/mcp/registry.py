"""Central tool registry. Tool modules call register(); the server reads it
for tools/list and tools/call."""

_TOOLS = {}


def register(schema, handler):
    _TOOLS[schema["name"]] = (schema, handler)


def schemas():
    return [schema for schema, _ in _TOOLS.values()]


def handler(name):
    entry = _TOOLS.get(name)
    return entry[1] if entry else None
