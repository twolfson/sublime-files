#!/usr/bin/env bash
# Exit on first failing command
set -e

# List all the files in our directory
for file in *; do
  # If the file is reserved, then skip it
  if echo "$file" | grep -E "^(.git|.gitignore|CHANGELOG.md|README.md|UNLICENSE|delete-sublime.sh|download-eula.sh|extract-sublime.sh|release.sh)$" &> /dev/null; then
    continue
  fi

  # Otherwise, remove it
  rm -r "$file"
done

# Notify the user that we are done
echo "Deletion complete. Please run \`git status\` to see what has changed." 1>&2
