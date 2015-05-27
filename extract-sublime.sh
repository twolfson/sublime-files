#!/usr/bin/env bash
# Exit on first failing command
set -e

# Handle our parameters
url="$1"
if test -z "$url"; then
  echo "Expected <url> parameter but it was not provided. Please provide a download URL for a Sublime Text tarball" 1>&2
  echo "Usage: ./extract-sublime.sh <url>" 1>&2
  exit 1
fi

# Create a temporary folder to work in
if test -d "tmp/"; then
  rm -r tmp/
fi
mkdir tmp/

# Download our package
cd tmp/
wget "$url"

# Extract the package
filename="$(basename "$url")"
tar xf "$filename"

# Enter our directory
subl_dir="sublime_text_3"
cd "$subl_dir"

# Find and remove files over 1MB (e.g. `plugin_host`, `sublime_text`)
for file in *; do
  # If it's a file (e.g. not a folder/symlink)
  if test -f "$file"; then
    # Get its size
    #  `du $file | cut --fields 1`: `4172 plugin_host` -> `4172` (kb)
    filesize="$(du "$file" | cut --fields 1)"

    # If it's over 1MB, then remove it
    if test "$filesize" -ge 1024; then
      echo "Removing $file due to being over 1MB" 1>&2
      rm "$file"
    fi
  fi
done
