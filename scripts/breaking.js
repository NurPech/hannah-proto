#!/usr/bin/env node

const { execSync } = require('child_process');
const path = require('path');

process.chdir(path.resolve(__dirname, '..'));

function run(command) {
    return execSync(command, { encoding: 'utf8' }).trim();
}

const latestTag = run("git tag --list \"v*\" --sort=-creatordate").split('\n')[0];
if (!latestTag) {
    console.error('No tags found.');
    process.exit(1);
}

console.log(`Against: ${latestTag}`);

// Only the current generation hannah/v2/ may change (hannah-proto#11, #19):
// hannah/v1/ is frozen as N−1, and so is the shared options.proto — same check
// as the lint:buf CI job. Deletions are allowed (how an old generation leaves).
const frozenChanges = run(`git diff --name-only --diff-filter=d ${latestTag} -- hannah/ ":!hannah/v2/"`);
if (frozenChanges) {
    console.error('hannah/v1/ and options.proto are frozen (N−1). Make changes in hannah/v2/ instead. Changed:');
    console.error(frozenChanges);
    process.exit(1);
}

execSync('buf lint', { stdio: 'inherit' });
execSync(`buf breaking --against ".git#tag=${latestTag}"`, { stdio: 'inherit' });
