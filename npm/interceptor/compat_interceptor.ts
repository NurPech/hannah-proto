/**
 * Per-message compatibility check (hannah-proto#9, hannah#217).
 *
 * DRAFT / template — not wired into anything consuming it yet, needs
 * review before use. See python/hannah_proto/compat_interceptor.py for the
 * full design rationale (kept there as the canonical explanation, not
 * repeated here to avoid drift between copies).
 *
 * REQUIRED_COMPAT_VERSIONS comes from generated `./compat_versions`
 * (scripts/gen-compat-versions.js, run by generate.sh) rather than from
 * runtime reflection on the generated message types — ts-proto is
 * configured without `outputSchema`, so there is no descriptor/options
 * data available on the generated types to read compat_version off of
 * directly (unlike the Python/Go versions). See gen-compat-versions.js's
 * header comment for what's unverified there.
 */
import type {
  Interceptor,
  InterceptorOptions,
  Listener,
  Metadata,
  NextCall,
} from "@grpc/grpc-js";
import { InterceptingCall } from "@grpc/grpc-js";

import { DEFAULT_COMPAT_VERSION, REQUIRED_COMPAT_VERSIONS } from "./compat_versions";

export const COMPAT_VERSION_METADATA_KEY = "x-compat-version";
export { DEFAULT_COMPAT_VERSION };

/** `methodName` is the bare RPC name (e.g. "SubmitText"), matching the keys
 * gen-compat-versions.js writes into REQUIRED_COMPAT_VERSIONS. */
function getRequiredCompatVersion(methodName: string): number {
  return REQUIRED_COMPAT_VERSIONS[methodName] ?? DEFAULT_COMPAT_VERSION;
}

/**
 * grpc-js client interceptor: attaches x-compat-version metadata to every
 * outgoing call, derived from the RPC method being invoked — so the server
 * only has to reject calls genuinely affected by a breaking change, not
 * every call after any unrelated schema change anywhere (see
 * hannah-proto#9, the SetGroupRooms incident).
 */
export const compatVersionInterceptor: Interceptor = (
  options: InterceptorOptions,
  nextCall: NextCall,
) => {
  const methodName = options.method_definition.path.split("/").pop() ?? "";
  const required = getRequiredCompatVersion(methodName);

  return new InterceptingCall(nextCall(options), {
    start(metadata: Metadata, listener: Listener, next) {
      metadata.set(COMPAT_VERSION_METADATA_KEY, String(required));
      next(metadata, listener);
    },
  });
};
