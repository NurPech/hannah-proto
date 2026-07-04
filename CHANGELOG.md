# Changelog
<!--
    Placeholder for the next version (at the beginning of the line):
    ## **WORK IN PROGRESS**
-->


## **WORK IN PROGRESS**

## 0.3.0
* Added: CI now gates MRs on `buf lint`/`buf breaking`; a breaking change must bump the new `PROTO_VERSION` file to pass — clients and Hannah are meant to exchange it on every call to reject a schema mismatch at runtime
* Added: CI publishes Python gRPC stubs to this project's PyPI package registry on tag (pilot for moving consumers off the git-submodule pattern; submodule usage still works alongside it)

## 0.2.0
* Added: `CHANGELOG.md` and `scripts/release.js` (copied unchanged from the Hannah monorepo, same script already reused by `hannah-timer`) — releases/tags are now cut consistently via `node scripts/release.js <patch|minor|major>` instead of manually (Refs #1)
* **Breaking**: `TimerCreate`/`TimerInfo` replace the fixed `room`/`roomie_id` fields (now `reserved`) with a generic `metadata` map; `TimerFired` echoes `metadata` back verbatim, removing the need for the Timer Service to look values up in Hannah's own store
