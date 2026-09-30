"""hannah.v2 — the current API generation (N), with the typed device model
(hannah-proto#19).

`hannah.v1` is frozen as N−1 next to it; both can be imported in the same
process, nothing collides in the descriptor pool (see hannah_proto.v1).
`hannah/options.proto` is shared, not copied.

    from hannah_proto.v2 import hannah_pb2, hannah_pb2_grpc
"""
import pkgutil

from . import hannah_pb2

# Same re-export as hannah_proto.v1: make every scope module's public names
# reachable via hannah_pb2, so `pb.EventFilter(...)` works for v2 too.
for _module_info in pkgutil.iter_modules(__path__):
    _name = _module_info.name
    if not _name.endswith("_pb2") or _name == "hannah_pb2":
        continue
    _module = __import__(f"hannah_proto.v2.{_name}", fromlist=["_"])
    for _attr in dir(_module):
        if not _attr.startswith("_") and not hasattr(hannah_pb2, _attr):
            setattr(hannah_pb2, _attr, getattr(_module, _attr))
del _module_info, _name, _module, _attr
