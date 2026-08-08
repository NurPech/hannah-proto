#!/bin/sh
# Regenerates npm/src from the .proto files one directory up.
# Run via `npm run buf` (or `npm run build`, which calls this first).
set -e

BUF_VERSION="1.71.0"
BUF_SHA256="d3de2838c68a5759ca276884254bc70df4e4ad185d6ed5f65f327b6ce6363eab"

cd "$(dirname "$0")/.."

if command -v buf >/dev/null 2>&1; then
  BUF="$(command -v buf)"
else
  BUF="/tmp/buf-hannah-proto"
  curl -sSL -o "$BUF" "https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-Linux-x86_64"
  echo "${BUF_SHA256}  ${BUF}" | sha256sum -c -
  chmod +x "$BUF"
fi

rm -rf src
# buf must run from the repo root (where buf.yaml/buf.gen.ts.yaml live) —
# from inside npm/, buf treats this directory as its own module input.
(cd .. && "$BUF" generate --template buf.gen.ts.yaml --output .)

# ts-proto mirrors the source .proto directory (hannah/) into the output —
# flatten back to a single directory so index.ts's barrel loop below (and
# every published import path) stays exactly as before the proto move.
mv src/hannah/* src/
rmdir src/hannah

# Per-method compat_version map (hannah-proto#9) — generated from the
# current schema via buf's own JSON descriptor output, not from ts-proto
# (outputSchema is off, so the generated types above carry no
# descriptor/options data of their own). See gen-compat-versions.js.
BUF_BIN="$BUF" node scripts/gen-compat-versions.js

# Hand-written source that ships alongside the generated stubs above,
# outside src/ so the `rm -rf src` at the top of this script never touches
# it (see npm/interceptor/). Copied in after generation, before the
# barrel-export loop below, so it's picked up the same way as any
# generated file.
cp interceptor/*.ts src/

echo "export const PROTO_VERSION = $(cat ../PROTO_VERSION);" > src/version.ts

{
  echo "export * from './version';"
  # Named-namespace re-export: every generated file declares its own
  # protobufPackage constant (same proto package in every file), so a
  # plain `export *` collides across modules. Namespacing avoids that.
  for f in src/*.ts; do
    base="$(basename "$f" .ts)"
    if [ "$base" = "version" ] || [ "$base" = "index" ]; then continue; fi
    echo "export * as ${base} from './${base}';"
  done
} > src/index.ts
