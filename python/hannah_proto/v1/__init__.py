"""hannah.v1 — the first versioned API generation (hannah-proto#11).

Frozen as N−1 since hannah.v2 (hannah-proto#19); the unversioned `hannah` package
it used to sit next to is gone. `hannah_proto.v1` and `hannah_proto.v2` can be
imported in the same process: their proto packages (`hannah.v1` vs `hannah.v2`)
and file names (`hannah/v1/x.proto` vs `hannah/v2/x.proto`) differ, so nothing
collides in the descriptor pool. `hannah/options.proto` is shared, not copied —
the compat_version extension exists only once.

    from hannah_proto.v1 import hannah_pb2, hannah_pb2_grpc
"""
import pkgutil

from . import hannah_pb2

# Same re-export as hannah_proto/__init__.py: make every scope module's public
# names reachable via hannah_pb2, so `pb.EventFilter(...)` works for v1 too.
for _module_info in pkgutil.iter_modules(__path__):
    _name = _module_info.name
    if not _name.endswith("_pb2") or _name == "hannah_pb2":
        continue
    _module = __import__(f"hannah_proto.v1.{_name}", fromlist=["_"])
    for _attr in dir(_module):
        if not _attr.startswith("_") and not hasattr(hannah_pb2, _attr):
            setattr(hannah_pb2, _attr, getattr(_module, _attr))
del _module_info, _name, _module, _attr
