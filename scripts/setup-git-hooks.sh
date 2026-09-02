#!/bin/sh
set -eu

git config core.hooksPath .githooks
chmod +x .githooks/pre-push

echo "Git hooks enabled."
echo "Direct pushes to main and develop are now blocked locally."
