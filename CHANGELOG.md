# Changelog
<!--
    Placeholder for the next version (at the beginning of the line):
    ## **WORK IN PROGRESS**
-->


## 0.2.0
* Added: `CHANGELOG.md` and `scripts/release.js` (copied unchanged from the Hannah monorepo, same script already reused by `hannah-timer`) — releases/tags are now cut consistently via `node scripts/release.js <patch|minor|major>` instead of manually (Refs #1)
* **Breaking**: `TimerCreate`/`TimerInfo` replace the fixed `room`/`roomie_id` fields (now `reserved`) with a generic `metadata` map; `TimerFired` echoes `metadata` back verbatim, removing the need for the Timer Service to look values up in Hannah's own store
