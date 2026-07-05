import pkgutil

from ._version import PROTO_VERSION
from . import hannah_pb2

__all__ = ["PROTO_VERSION"]

# hannah.proto imports every other scope-split .proto file, but protoc's Python
# codegen keeps each file's messages/enums in that file's own generated module
# (agent_pb2, event_stream_pb2, ...) rather than re-exporting them into
# hannah_pb2. Existing consumer code (across every hannah-proto consumer, not
# just this package) expects every message reachable via hannah_pb2 — the
# behavior before hannah.proto was split by scope. Patch every scope module's
# public names onto hannah_pb2 here so `from hannah_proto import hannah_pb2 as
# pb; pb.EventFilter(...)` etc. keeps working without touching call sites.
# Discovered dynamically (not a hardcoded module list) so this doesn't need
# updating whenever a new scope file is added.
for _module_info in pkgutil.iter_modules(__path__):
    _name = _module_info.name
    if not _name.endswith("_pb2") or _name == "hannah_pb2":
        continue
    _module = __import__(f"hannah_proto.{_name}", fromlist=["_"])
    for _attr in dir(_module):
        if not _attr.startswith("_") and not hasattr(hannah_pb2, _attr):
            setattr(hannah_pb2, _attr, getattr(_module, _attr))
del _module_info, _name, _module, _attr
