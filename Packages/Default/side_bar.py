import os
import functools

import sublime
import sublime_plugin


class NewFileAtCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        v = self.window.new_file()

        if len(dirs) == 1:
            v.settings().set('default_dir', dirs[0])

    def is_visible(self, dirs):
        return len(dirs) == 1


class NewFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("Folder Name:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        os.makedirs(os.path.join(dir, name), 0o775)

    def is_visible(self, dirs):
        return len(dirs) == 1


class RenamePathCommand(sublime_plugin.WindowCommand):
    def run(self, paths):
        branch, leaf = os.path.split(paths[0])
        v = self.window.show_input_panel(
            "New Name:",
            leaf,
            functools.partial(self.on_done, paths[0], branch),
            None,
            None)
        name, ext = os.path.splitext(leaf)

        v.sel().clear()
        v.sel().add(sublime.Region(0, len(name)))

    def is_case_change(self, old, new):
        if old.lower() != new.lower():
            return False
        if os.stat(old).st_ino != os.stat(new).st_ino:
            return False
        return True

    def on_done(self, old, branch, leaf):
        new = os.path.join(branch, leaf)

        if new == old:
            return

        try:
            if os.path.isfile(new) and not self.is_case_change(old, new):
                raise OSError("File already exists")

            os.rename(old, new)

            v = self.window.find_open_file(old)
            if v:
                v.retarget(new)
        except OSError as e:
            sublime.status_message("Unable to rename: " + str(e))
        except:
            sublime.status_message("Unable to rename")

    def is_visible(self, paths):
        return len(paths) == 1


class OpenContainingFolderCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        branch, leaf = os.path.split(files[0])

        # Open dir expands variables, and allows escaping to prevent expansion,
        # but because of this UNC paths which look like an escaped single
        # backslash need to be escaped
        if os.name == 'nt' and branch.startswith(r'\\'):
            branch = r'\\' + branch

        self.window.run_command("open_dir", {"dir": branch, "file": leaf})

    def is_visible(self, files):
        return len(files) > 0


class OpenFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        for d in dirs:
            self.window.run_command("open_dir", {"dir": d})

    def is_visible(self, dirs):
        return len(dirs) > 0


class FindInFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.run_command(
            "show_panel",
            {
                "panel": "find_in_files",
                "where": ",".join(dirs + ["<project filters>"])
            }
        )

    def is_visible(self, dirs):
        return len(dirs) > 0
