# hannah-proto

Protobuf/gRPC schema definitions for the Hannah voice assistant ecosystem (Core, satellites, WebUI, ioBroker adapter, Telegram bot, and other consumers). This repo is the single source of truth for the wire protocol shared across all of them.

The `.proto` files live under `hannah/`, one per functional area — satellite control, event streaming, the ioBroker agent bridge, user registry, timers, automations, and so on. Nothing here is application code, just schema.

## Distribution

Three independent, tag-triggered publish targets — pick whichever matches your language. Each contains only generated gRPC stubs/types for the current tagged release.

| Language   | Package                                 | Install                                    |
|------------|------------------------------------------|---------------------------------------------|
| Python     | PyPI [`hannah-proto`](https://pypi.org/project/hannah-proto/) | `pip install hannah-proto` |
| TypeScript | npm [`@m1kad0/hannah-proto`](https://www.npmjs.com/package/@m1kad0/hannah-proto) | `npm install @m1kad0/hannah-proto` |
| Go         | [github.com/NurPech/hannah-proto-go](https://github.com/NurPech/hannah-proto-go) | `go get github.com/NurPech/hannah-proto-go` |

Go has no separate package registry, so that tagged GitHub repo *is* the package — `go get` resolves it directly.

## API generations: hannah.v1

The schema exists in two packages side by side:

| Package | Files | Status |
|---|---|---|
| `hannah.v1` | `hannah/v1/*.proto` | **current generation** — all changes go here |
| `hannah` (unversioned) | `hannah/*.proto` | frozen (N−1), kept so older components keep working |

Both carry the same services and messages, but under different gRPC method paths (`/hannah.v1.HannahService/...` vs `/hannah.HannahService/...`), so a server can serve both at once and gRPC routes each call to the right one. Hannah Core serves the current generation and the one before it (N and N−1, never more). Clients use the current generation and fall back to the previous one if Core answers `UNIMPLEMENTED` (Core too old).

A breaking change never happens inside a generation — it starts the next one (`hannah.v2`), and the oldest one is removed. `hannah/options.proto` (the `compat_version` extension) is shared by both packages, not copied. The API generation is independent of the package version: `hannah.v1` ships in 4.x.

| Language | Current generation | Previous generation |
|---|---|---|
| Python | `from hannah_proto.v1 import hannah_pb2` | `from hannah_proto import hannah_pb2` |
| TypeScript | `import { v1 } from '@m1kad0/hannah-proto'` → `v1.agent.AgentMessage` | `import { agent } from '@m1kad0/hannah-proto'` |
| Go | `github.com/NurPech/hannah-proto-go/v4/hannahv1` | `github.com/NurPech/hannah-proto-go/v4` |

CI rejects any change under `hannah/` outside `hannah/v1/`.

## Versioning: PROTO_VERSION

Alongside the semver package/tag version, every release carries a single-integer `PROTO_VERSION` (see the `PROTO_VERSION` file). Hannah Core and its clients exchange this value on every call and reject a mismatch at runtime — that's the actual compatibility gate, not the semver tag. A breaking schema change requires bumping `PROTO_VERSION`; CI enforces this on every merge request via `buf breaking`.

## Per-message compatibility: compat_version

`PROTO_VERSION` is repo-wide — any breaking change anywhere bumps it, forcing every consumer to reject, even ones that never call the affected RPC. `compat_version` (`options.proto`) is a finer-grained, independent counter set on an individual message:

```proto
message Foo {
  option (compat_version) = 2;
  ...
}
```

Bump a message's `compat_version` only when *that specific message* has an actual breaking change. A message with no `compat_version` option carries an implicit value of `1` — don't backfill the option onto messages that have never had a breaking change. This lets a consumer-side interceptor check only the messages a given RPC call actually uses instead of rejecting on any unrelated proto change.

## Deprecating fields and RPCs

Don't remove a field or RPC the moment it's unused — that forces every consumer to bump immediately, even ones that never touched it (see the `SetGroupRooms` incident that forced 9 unrelated components to bump, `hannah-proto#9`). Instead:

1. Mark it `deprecated = true` (protobuf's built-in field/method option) and note why + what replaces it in a comment.
2. Leave it in place until the next planned major cleanup, not the next release.
3. Actually remove it (a breaking change, `PROTO_VERSION` bump) only during that cleanup, batched with other accumulated deprecations rather than one at a time.

Go/TypeScript/Python codegen surface `deprecated = true` automatically (Go doc comment, TS `@deprecated` JSDoc) — no extra tooling or config needed.

## Compatibility checks

CI runs `buf lint` and `buf breaking` (against `origin/master`) on every MR. To check a local branch against a specific released version:

```sh
buf breaking --against '.git#tag=vX.Y.Z'
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for what changed release to release, including breaking changes and the consumers they affect.
