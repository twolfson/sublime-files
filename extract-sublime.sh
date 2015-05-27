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

# For each of the Sublime packages
cd Packages/
for file in *; do
  # Extract the packages to its corresponding folder
  #   e.g. `ActionScript.sublime-package` -> `ActionScript`
  pkg_dir="$(echo "$file" | sed -E "s/.sublime-package//")"
  unzip -d "$pkg_dir" "$file";

  # Remove the original file
  rm "$file"
done
cd ../

# Perform a sanity check that no single file is over 1MB
shopt -s globstar
for file in **/*; do
  # If it's a file (e.g. not a folder/symlink)
  if test -f "$file"; then
    # Get its size
    #  `du $file | cut --fields 1`: `4172 plugin_host` -> `4172` (kb)
    filesize="$(du "$file" | cut --fields 1)"

    # If it's over 1MB, then complain about it
    if test "$filesize" -ge 1024; then
      echo "WARNING: $file is over 1MB large" 1>&2
    fi
  fi
done
shopt -u globstar

# Transfer our files
#   `ls` -> `sublime_text_3 sublime_text_3_build_3083_x64.tar.bz2`
cd ../
cp sublime_text_3/* ../ -R

# Navigate out of our temporary directory and notify the user that we are done
echo "Extraction complete. Please run \`git status\` to see what has changed." 1>&2
