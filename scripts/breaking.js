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

// The unversioned hannah package is frozen since hannah.v1 exists (N−1,
// hannah-proto#11) — same check as the lint:buf CI job.
const frozenChanges = run(`git diff --name-only ${latestTag} -- hannah/ ":!hannah/v1/"`);
if (frozenChanges) {
    console.error('The unversioned hannah package is frozen (N−1). Make changes in hannah/v1/ instead. Changed:');
    console.error(frozenChanges);
    process.exit(1);
}

execSync('buf lint', { stdio: 'inherit' });
execSync(`buf breaking --against ".git#tag=${latestTag}"`, { stdio: 'inherit' });
