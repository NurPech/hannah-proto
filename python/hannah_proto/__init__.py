"""hannah_proto — Protobuf/gRPC stubs for the Hannah voice assistant.

The API lives in versioned generations since hannah.v1 (hannah-proto#11):

    from hannah_proto.v2 import hannah_pb2, hannah_pb2_grpc   # current (N)
    from hannah_proto.v1 import hannah_pb2, hannah_pb2_grpc   # previous (N−1, frozen)

The unversioned `hannah` package that used to live at this level is gone since
hannah.v2 (hannah-proto#19); only the shared options.proto (`compat_version`)
is left at the package root.
"""
from ._version import PROTO_VERSION

__all__ = ["PROTO_VERSION"]
