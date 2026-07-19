# hannah-proto

Protobuf/gRPC schema definitions for the Hannah voice assistant ecosystem (Core, satellites, WebUI, ioBroker adapter, Telegram bot, and other consumers). This repo is the single source of truth for the wire protocol shared across all of them.

The `.proto` files live flat at the repo root, one per functional area — satellite control, event streaming, the ioBroker agent bridge, user registry, timers, automations, and so on. Nothing here is application code, just schema.

## Distribution

Three independent, tag-triggered publish targets — pick whichever matches your language. Each contains only generated gRPC stubs/types for the current tagged release.

| Language   | Package                                 | Install                                    |
|------------|------------------------------------------|---------------------------------------------|
| Python     | PyPI [`hannah-proto`](https://pypi.org/project/hannah-proto/) | `pip install hannah-proto` |
| TypeScript | npm [`@m1kad0/hannah-proto`](https://www.npmjs.com/package/@m1kad0/hannah-proto) | `npm install @m1kad0/hannah-proto` |
| Go         | [github.com/NurPech/hannah-proto-go](https://github.com/NurPech/hannah-proto-go) | `go get github.com/NurPech/hannah-proto-go` |

Go has no separate package registry, so that tagged GitHub repo *is* the package — `go get` resolves it directly.

## Versioning: PROTO_VERSION

Alongside the semver package/tag version, every release carries a single-integer `PROTO_VERSION` (see the `PROTO_VERSION` file). Hannah Core and its clients exchange this value on every call and reject a mismatch at runtime — that's the actual compatibility gate, not the semver tag. A breaking schema change requires bumping `PROTO_VERSION`; CI enforces this on every merge request via `buf breaking`.

## Compatibility checks

CI runs `buf lint` and `buf breaking` (against `origin/master`) on every MR. To check a local branch against a specific released version:

```sh
buf breaking --against '.git#tag=vX.Y.Z'
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for what changed release to release, including breaking changes and the consumers they affect.
