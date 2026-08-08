package hannahproto

// Per-message compatibility check (hannah-proto#9, hannah#217).
//
// DRAFT / template — not wired into the CI publish pipeline yet, needs
// review before use. See python/hannah_proto/compat_interceptor.py for the
// full design rationale (kept there as the canonical explanation, not
// repeated here to avoid drift between copies).
//
// Go consumers of this package (Proxy) are gRPC *clients*, never the
// server — Core (Python) is the only server, so only client interceptors
// are needed here. Mirrors Python's approach exactly: build a static
// method-path -> required-compat_version map once, from the service
// descriptor via the global protobuf registry, rather than reading
// compat_version off concrete request/response message instances. That's
// what makes this work uniformly for both unary AND streaming RPCs
// (RegisterProxy is a bidi stream) — a streaming client interceptor only
// ever sees the method name, never a single request/response pair.

import (
	"context"
	"fmt"
	"strconv"
	"sync"

	"google.golang.org/grpc"
	"google.golang.org/grpc/metadata"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/reflect/protoreflect"
	"google.golang.org/protobuf/reflect/protoregistry"
)

// CompatVersionMetadataKey is the gRPC metadata key carrying the
// compat_version this client's schema assumes for the messages a given
// call uses.
const CompatVersionMetadataKey = "x-compat-version"

// DefaultCompatVersion is the implicit version for messages without an
// explicit compat_version option (see options.proto) — matches the
// "absent means 1" convention documented there.
const DefaultCompatVersion int32 = 1

// hannahServiceFullName must match the `package` + `service` declaration
// in hannah.proto (package hannah; service HannahService).
const hannahServiceFullName protoreflect.FullName = "hannah.HannahService"

var (
	requiredVersionsOnce sync.Once
	requiredVersions     map[string]int32
	requiredVersionsErr  error
)

// messageCompatVersion reads the compat_version option off a single
// message descriptor, or DefaultCompatVersion if unset.
//
// NEEDS VERIFICATION: E_CompatVersion is the protoc-gen-go extension
// variable name I *expect* for `extend google.protobuf.MessageOptions {
// int32 compat_version = 50000; }` (options.proto), following the usual
// E_<FieldName> convention — but there's no generated Go code checked into
// this repo to confirm against (publish:go generates into a scratch dir,
// nothing committed). Confirm the actual name once codegen runs.
func messageCompatVersion(md protoreflect.MessageDescriptor) int32 {
	opts := md.Options()
	if opts == nil {
		return DefaultCompatVersion
	}
	msgOpts, ok := opts.(proto.Message)
	if !ok || !proto.HasExtension(msgOpts, E_CompatVersion) {
		return DefaultCompatVersion
	}
	v, _ := proto.GetExtension(msgOpts, E_CompatVersion).(int32)
	if v == 0 {
		return DefaultCompatVersion
	}
	return v
}

func requiredCompatVersion(method protoreflect.MethodDescriptor) int32 {
	in := messageCompatVersion(method.Input())
	out := messageCompatVersion(method.Output())
	if in > out {
		return in
	}
	return out
}

// buildRequiredVersions builds the method-path -> required-compat_version
// map once (lazily, on first use — cheap enough, no reason to force it at
// package init and risk ordering issues with the registering package's
// own init()).
func buildRequiredVersions() (map[string]int32, error) {
	requiredVersionsOnce.Do(func() {
		d, err := protoregistry.GlobalFiles.FindDescriptorByName(hannahServiceFullName)
		if err != nil {
			requiredVersionsErr = fmt.Errorf("compat_interceptor: HannahService descriptor not found (was the generated package imported for its registration side effect?): %w", err)
			return
		}
		service, ok := d.(protoreflect.ServiceDescriptor)
		if !ok {
			requiredVersionsErr = fmt.Errorf("compat_interceptor: %s is not a service descriptor", hannahServiceFullName)
			return
		}
		out := make(map[string]int32, service.Methods().Len())
		methods := service.Methods()
		for i := 0; i < methods.Len(); i++ {
			m := methods.Get(i)
			out[fmt.Sprintf("/%s/%s", service.FullName(), m.Name())] = requiredCompatVersion(m)
		}
		requiredVersions = out
	})
	return requiredVersions, requiredVersionsErr
}

func compatVersionMetadataValue(method string) string {
	versions, err := buildRequiredVersions()
	if err != nil {
		// Don't block calls on a bug in this mechanism itself — fall back to
		// the implicit default, same as an old client that predates it.
		return strconv.Itoa(int(DefaultCompatVersion))
	}
	if v, ok := versions[method]; ok {
		return strconv.Itoa(int(v))
	}
	return strconv.Itoa(int(DefaultCompatVersion))
}

// CompatVersionUnaryClientInterceptor attaches x-compat-version metadata to
// every outgoing unary call, derived from the request/response message
// types the invoked method actually uses — so the server only has to
// reject calls genuinely affected by a breaking change, not every call
// after any unrelated schema change anywhere (see hannah-proto#9, the
// SetGroupRooms incident).
func CompatVersionUnaryClientInterceptor(
	ctx context.Context,
	method string,
	req, reply interface{},
	cc *grpc.ClientConn,
	invoker grpc.UnaryInvoker,
	opts ...grpc.CallOption,
) error {
	ctx = metadata.AppendToOutgoingContext(ctx, CompatVersionMetadataKey, compatVersionMetadataValue(method))
	return invoker(ctx, method, req, reply, cc, opts...)
}

// CompatVersionStreamClientInterceptor is the streaming equivalent —
// covers RegisterProxy (bidi stream) the same way, since the required
// version is looked up by method path, not by inspecting a message
// instance that a stream never hands the interceptor as a single value.
func CompatVersionStreamClientInterceptor(
	ctx context.Context,
	desc *grpc.StreamDesc,
	cc *grpc.ClientConn,
	method string,
	streamer grpc.Streamer,
	opts ...grpc.CallOption,
) (grpc.ClientStream, error) {
	ctx = metadata.AppendToOutgoingContext(ctx, CompatVersionMetadataKey, compatVersionMetadataValue(method))
	return streamer(ctx, desc, cc, method, opts...)
}
