"""hannah.v1 — the first versioned API generation (hannah-proto#11).

Lives next to the unversioned `hannah` package (hannah_proto itself), which is
frozen as N−1. Both can be imported in the same process: their proto packages
(`hannah` vs `hannah.v1`) and file names (`hannah/x.proto` vs `hannah/v1/x.proto`)
differ, so nothing collides in the descriptor pool. `hannah/options.proto` is
shared, not copied — the compat_version extension exists only once.

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
