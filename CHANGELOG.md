# Changelog
<!--
    Placeholder for the next version (at the beginning of the line):
    ## **WORK IN PROGRESS**
-->


## **WORK IN PROGRESS**

## 0.5.0
* **Breaking**: Removed `GetRoutines`/`CreateRoutine`/`UpdateRoutine`/`DeleteRoutine` RPCs and their messages (`Routine`, `GetRoutinesResponse`, `CreateRoutineRequest`, `CreateRoutineResponse`, `UpdateRoutineRequest`, `DeleteRoutineRequest`) from `control.proto` — Hannah Core retired the standalone "Routines" concept in favor of a `when.phrase` Trigger condition (`hannah#139`) and no longer implements these RPCs. Consumers still calling them (e.g. the WebUI routine editor) need their own follow-up before upgrading to this version.

## 0.4.0
* Added: `StateType` enum + `EnumValues` message (`shared.proto`) — classifies an ioBroker state's value (`BOOLEAN`/`NUMERIC`/`ENUM`/`COLOR`/`TEXT`) so consumers can offer the right operators/input widget instead of a free-text state ID. Wired into `AgentDevice` (`agent.proto`, adapter → Core) and `DeviceInfo` (`device_control_menu.proto`, `GetDevices` response) as `state_type`/`enum_values` resp. `state_types`/`state_enum_values` maps. Prep for `hannah#117` / `hannah-webui#16`'s trigger editor

## 0.3.9
* Fixed: `python/pyproject.toml`'s `grpcio`/`protobuf` dependency floors (`>=1.60`/`>=4.25`) were far looser than what the actually-generated gencode requires — a plain `pip install hannah-proto` could resolve a runtime too old to import the package at all (`VersionError`/`RuntimeError` at import time). Raised to `grpcio>=1.82.1`/`protobuf>=7.35.0` to match 0.3.8's gencode; still needs bumping by hand alongside any future CI toolchain upgrade that changes the generated version markers

## 0.3.8
* Added: `User.enabled_automations`, `SetAutomation` RPC (`user_registry.proto`) and `AutomationConnect` bidirectional stream (`automation.proto`) — lets an external automation service (e.g. `telegram_autoresponder`) register itself, receive a snapshot of users with it currently enabled, and get live updates, without depending on the generic `SubscribeEvents` bus

## 0.3.7
* Added: `GetTimers`/`DeleteTimer` RPCs (`timer_admin.proto`) — query and cancel a user's active timers independent of the `TimerConnect` stream, e.g. for an Admin-UI or Telegram bot

## 0.3.6
* Fixed: `@m1kad0/hannah-proto`'s npm package was missing `@bufbuild/protobuf` as a real dependency — the generated `@grpc/grpc-js` service/client code needs it at runtime for wire encode/decode, but it was only ever present transitively as a `ts-proto` dev dependency, so a plain `npm install @m1kad0/hannah-proto` left consumers with `Error: Cannot find module '@bufbuild/protobuf/wire'` at runtime (not caught by `tsc --noEmit` on the consumer side)

## 0.3.5
* Fixed: `hannah_proto`'s `__init__.py` now re-exports every scope-split module's messages/enums onto `hannah_pb2` (dynamically discovered via `pkgutil`, not a hardcoded list) — without this, `hannah_pb2.EventFilter` and every other message defined outside `hannah.proto` itself raised `AttributeError` for any consumer expecting the pre-split, single-module behavior. Same fix `core`/`telegram` in the `hannah` monorepo already carry locally; this makes it unnecessary for future Python consumers of this package

## 0.3.4
* Changed: `@m1kad0/hannah-proto` now generates real `@grpc/grpc-js`-compatible service clients (`ts-proto` `outputServices=grpc-js`, `forceLong=bigint`) instead of bare message types — usable as a drop-in for consumers currently doing dynamic `@grpc/proto-loader` loading. `@grpc/grpc-js` is a peerDependency. Also excludes `npm/node_modules` from `buf`'s module scan, since installing `@grpc/grpc-js`/`protobufjs` pulls in their own vendored `.proto` files that `buf` was otherwise picking up and failing to build

## 0.3.3
* Added: CI publishes generated TypeScript types to the public npm registry (`@m1kad0/hannah-proto`) on tag — pilot for TS/npm consumers, third distribution channel alongside PyPI and Go. `ts-proto` emits types only (no service/client code); the codegen itself lives in `npm/scripts/generate.sh` (`npm run buf` / `npm run build`) rather than inline in CI

## 0.3.2
* Added: `publish:go` now also generates `version.go` (`hannahproto.ProtoVersion`), matching `hannah_proto.PROTO_VERSION` on the PyPI side — the Go module was published without any way to read `PROTO_VERSION` at runtime

## 0.3.1
* **Breaking**: `go_package` changed from `dev.kernstock.net/.../hannah/proxy/proto/hannah` to `github.com/NurPech/hannah-proto-go;hannahproto` — the internal Go proxy consumer must update its import path
* Added: CI generates Go gRPC stubs and publishes them to the public `github.com/NurPech/hannah-proto-go` repo on tag — Go has no package registry, so the tagged public repo itself is the distribution channel `go get` resolves
* Changed: `publish:pypi` now uploads to the real public PyPI (`pypi.org`) instead of this project's GitLab package registry — self-hosters of the public Hannah need `pip install` to work without GitLab credentials

## 0.3.0
* Added: CI now gates MRs on `buf lint`/`buf breaking`; a breaking change must bump the new `PROTO_VERSION` file to pass — clients and Hannah are meant to exchange it on every call to reject a schema mismatch at runtime
* Added: CI publishes Python gRPC stubs to this project's PyPI package registry on tag (pilot for moving consumers off the git-submodule pattern; submodule usage still works alongside it)

## 0.2.0
* Added: `CHANGELOG.md` and `scripts/release.js` (copied unchanged from the Hannah monorepo, same script already reused by `hannah-timer`) — releases/tags are now cut consistently via `node scripts/release.js <patch|minor|major>` instead of manually (Refs #1)
* **Breaking**: `TimerCreate`/`TimerInfo` replace the fixed `room`/`roomie_id` fields (now `reserved`) with a generic `metadata` map; `TimerFired` echoes `metadata` back verbatim, removing the need for the Timer Service to look values up in Hannah's own store
