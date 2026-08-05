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
execSync('buf lint', { stdio: 'inherit' });
execSync(`buf breaking --against ".git#tag=${latestTag}"`, { stdio: 'inherit' });
