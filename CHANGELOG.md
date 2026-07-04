# Changelog
<!--
    Placeholder for the next version (at the beginning of the line):
    ## **WORK IN PROGRESS**
-->





## **WORK IN PROGRESS**

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
