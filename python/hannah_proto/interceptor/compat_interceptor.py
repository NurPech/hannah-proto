"""
Per-message compatibility check (hannah-proto#9, hannah#217).

DRAFT / template — not wired into anything yet, needs review before use.

Complements the repo-wide PROTO_VERSION check (hannah.grpc_interceptors.
ProtocolVersionInterceptor): PROTO_VERSION bumps on *any* breaking change
anywhere in the schema, so gating every call on an exact PROTO_VERSION
match rejects clients that were never affected by whatever change bumped
it (see the SetGroupRooms incident, hannah-proto#9).

compat_version (options.proto) is a per-message counter, bumped only when
*that* message has an actual breaking change. This module derives, for a
given RPC method, the highest compat_version among the request/response
types it actually uses, and provides a server interceptor that checks a
client's declared compat_version against that instead of the global
counter.

Note on PROTO_VERSION: don't run both as hard per-call gates — that
reintroduces the exact problem this is meant to fix, since PROTO_VERSION
still climbs on every unrelated change. A client that never sends
x-compat-version is treated as compat_version 1 (see DEFAULT_COMPAT_VERSION
below), which already gates pre-compat_version clients on any method that
needs more than the implicit version — so PROTO_VERSION doesn't need to
stay in the runtime check path at all. It can keep existing purely for
`buf breaking` in CI and as a human-readable changelog marker.
"""
from __future__ import annotations

import collections
import logging
from typing import Dict, Tuple

import grpc
import grpc.aio
from google.protobuf.descriptor import Descriptor, MethodDescriptor, ServiceDescriptor

from .. import options_pb2  # generated from options.proto — verify this is the actual generated module/attribute name once codegen runs

log = logging.getLogger(__name__)

COMPAT_VERSION_METADATA_KEY = "x-compat-version"
DEFAULT_COMPAT_VERSION = 1  # implicit version for messages without the option (see options.proto)


def get_message_compat_version(descriptor: Descriptor) -> int:
    """compat_version of a single message type, or the implicit default."""
    options = descriptor.GetOptions()
    if options.HasExtension(options_pb2.compat_version):
        return options.Extensions[options_pb2.compat_version]
    return DEFAULT_COMPAT_VERSION


def required_compat_version(method: MethodDescriptor) -> int:
    """The compat_version a client needs to safely call this method: the
    max of its request and response type's compat_version."""
    return max(
        get_message_compat_version(method.input_type),
        get_message_compat_version(method.output_type),
    )


def build_required_versions(service: ServiceDescriptor) -> Dict[str, int]:
    """method full path ('/package.Service/Method') -> required
    compat_version, for every method on the given service. Computed once
    at interceptor construction time — cheap enough to redo per process
    start, no need to persist/cache across restarts."""
    return {
        f"/{service.full_name}/{method.name}": required_compat_version(method)
        for method in service.methods
    }


class CompatVersionInterceptor(grpc.ServerInterceptor):
    """Per-method compat_version gate. Mirrors ProtocolVersionInterceptor's
    enforce-toggle rollout pattern: enforce=False only logs mismatches,
    enforce=True rejects with FAILED_PRECONDITION before the handler runs.

    A missing x-compat-version header is treated as compat_version 1 —
    i.e. "this client predates the mechanism (or hasn't adopted it yet),
    only let through calls that never had a breaking change."
    """

    def __init__(self, service: ServiceDescriptor, enforce: bool = False):
        self._required = build_required_versions(service)
        self.enforce = enforce  # public: runtime-togglable, same pattern as ProtocolVersionInterceptor.enforce

    def intercept_service(self, continuation, handler_call_details):
        handler = continuation(handler_call_details)
        if handler is None:
            return handler

        required = self._required.get(handler_call_details.method)
        if required is None:
            # Unknown method — shouldn't happen once built off the real
            # service descriptor. Don't block on something we can't reason about.
            return handler

        metadata = dict(handler_call_details.invocation_metadata or ())
        raw = metadata.get(COMPAT_VERSION_METADATA_KEY)
        received = int(raw) if raw is not None else DEFAULT_COMPAT_VERSION

        if received >= required:
            return handler

        message = (
            f"compat_version mismatch on {handler_call_details.method!r}: "
            f"requires {required}, client declared {received}"
        )
        if not self.enforce:
            log.warning(f"[grpc/compat_version] {message} — logged only (enforce=False)")
            return handler

        log.warning(f"[grpc/compat_version] {message} — RPC rejected")
        return _make_abort_handler(handler, message)


def client_compat_version_metadata(service: ServiceDescriptor, method_name: str) -> Tuple[str, str]:
    """For client-side use: the (key, value) metadata tuple to attach to an
    outgoing call, so the server can evaluate it against its own (always
    current) schema. `method_name` is the bare RPC name, e.g. "SubmitText".
    Not yet wired into any of the 6 external clients — same gradual
    rollout story as x-proto-version originally had (#60)."""
    required = build_required_versions(service).get(
        f"/{service.full_name}/{method_name}", DEFAULT_COMPAT_VERSION
    )
    return (COMPAT_VERSION_METADATA_KEY, str(required))


class _ClientCallDetails(
    collections.namedtuple(
        "_ClientCallDetails",
        ("method", "timeout", "metadata", "credentials", "wait_for_ready"),
    ),
    grpc.aio.ClientCallDetails,
):
    pass


def _add_compat_version_metadata(client_call_details, value: str) -> _ClientCallDetails:
    metadata = list(client_call_details.metadata or [])
    metadata.append((COMPAT_VERSION_METADATA_KEY, value))
    return _ClientCallDetails(
        client_call_details.method,
        client_call_details.timeout,
        metadata,
        client_call_details.credentials,
        client_call_details.wait_for_ready,
    )


class CompatVersionClientInterceptor(
    grpc.aio.UnaryUnaryClientInterceptor,
    grpc.aio.UnaryStreamClientInterceptor,
    grpc.aio.StreamUnaryClientInterceptor,
    grpc.aio.StreamStreamClientInterceptor,
):
    """Ready-made grpc.aio client interceptor — attaches x-compat-version to
    every outgoing call, derived from the invoked method's request/response
    types (same map `CompatVersionInterceptor` builds server-side). Mirrors
    the shape of a plain `ProtocolVersionClientInterceptor`
    (x-proto-version) so an existing async Python client (e.g. Telegram)
    can adopt this the same way, without hand-rolling its own descriptor
    lookup — that's the reason this exists as a class here instead of
    leaving `client_compat_version_metadata` as the only option (see
    hannah-proto#10).
    """

    def __init__(self, service: ServiceDescriptor):
        self._required = build_required_versions(service)

    def _value_for(self, method: str) -> str:
        return str(self._required.get(method, DEFAULT_COMPAT_VERSION))

    async def intercept_unary_unary(self, continuation, client_call_details, request):
        value = self._value_for(client_call_details.method)
        return await continuation(_add_compat_version_metadata(client_call_details, value), request)

    async def intercept_unary_stream(self, continuation, client_call_details, request):
        value = self._value_for(client_call_details.method)
        return await continuation(_add_compat_version_metadata(client_call_details, value), request)

    async def intercept_stream_unary(self, continuation, client_call_details, request_iterator):
        value = self._value_for(client_call_details.method)
        return await continuation(_add_compat_version_metadata(client_call_details, value), request_iterator)

    async def intercept_stream_stream(self, continuation, client_call_details, request_iterator):
        value = self._value_for(client_call_details.method)
        return await continuation(_add_compat_version_metadata(client_call_details, value), request_iterator)


def _make_abort_handler(handler: "grpc.RpcMethodHandler", message: str) -> "grpc.RpcMethodHandler":
    # Same shape as hannah.grpc_interceptors._make_abort_handler, duplicated
    # here so this module has no dependency on Core's package.
    code = grpc.StatusCode.FAILED_PRECONDITION

    if handler.request_streaming and handler.response_streaming:
        def behavior(request_iterator, context):
            context.abort(code, message)
        return grpc.stream_stream_rpc_method_handler(
            behavior,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
    if handler.request_streaming and not handler.response_streaming:
        def behavior(request_iterator, context):
            context.abort(code, message)
        return grpc.stream_unary_rpc_method_handler(
            behavior,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )
    if not handler.request_streaming and handler.response_streaming:
        def behavior(request, context):
            context.abort(code, message)
        return grpc.unary_stream_rpc_method_handler(
            behavior,
            request_deserializer=handler.request_deserializer,
            response_serializer=handler.response_serializer,
        )

    def behavior(request, context):
        context.abort(code, message)
    return grpc.unary_unary_rpc_method_handler(
        behavior,
        request_deserializer=handler.request_deserializer,
        response_serializer=handler.response_serializer,
    )
