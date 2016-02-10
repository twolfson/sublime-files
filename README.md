# sublime-files
An extracted backup of Sublime Text's files.

This was initially inspired by [sublime-default][] but that fell short of having the non-default included Sublime Packages. As a result, I decided to set up this repo.

[sublime-default]: https://github.com/randy3k/sublime-default

## Why?
When writing plugins and researching Sublime Text's API, it's very useful to have a hosted and sharable reference for code comments and forum posts.

## You are out of date
Whoops! Please either create an issue or a pull request about that. If you would like to run the script, it can be run via:

```bash
# Remove all Sublime files
./delete-sublime.sh

# Download the latest EULA
./download-eula.sh

# Download/extract latest Sublime tarball
./extract-sublime.sh <url>
# For example:
# ./extract-sublime.sh http://c758482.r82.cf2.rackcdn.com/sublime_text_3_build_3083_x64.tar.bz2
```

URLs should be the portable tarballs provided for Sublime Text 3 from:

http://www.sublimetext.com/3

## Is this legal?
I am not a lawyer but yes, it should be legal. Under Sublime Text's EULA, we can host "backups and archival [copies]" of Sublime Text.

http://www.sublimetext.com/eula

Internally hosted EULA can be found here:

[EULA][]

The specific lines regarding "backups and archival [copies]" can be found here:

[Backups and archival lines](EULA#L38-L39)

[EULA]: EULA

## License
In accordance with Sublime Text's EULA, all files except for `.foundryrc`, `.gitignore`, `CHANGELOG.md`, `README.md`, `UNLICENSE`, `delete-sublime.sh`, `download-eula.sh`, `extract-sublime.sh`, and `release.sh` in this repository are owned by SUBLIME HQ PTY LTD.

Here are the specific lines regarding that ownership:

[Copyright lines](EULA#L53-L54)

With respect to the excepted files (`.foundryrc`, `.gitignore`, `CHANGELOG.md`, `README.md`, `UNLICENSE`, `delete-sublime.sh`, `download-eula.sh`, `extract-sublime.sh`, `release.sh`), those are released to the Public Domain by Todd Wolfson under the [UNLICENSE][].

[UNLICENSE]: UNLICENSE
