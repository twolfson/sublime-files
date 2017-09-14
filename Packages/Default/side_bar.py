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


class DeleteFileCommand(sublime_plugin.WindowCommand):
    def run(self, files):
        # Import send2trash on demand, to avoid initialising ctypes for as long as possible
        import Default.send2trash as send2trash
        for f in files:
            v = self.window.find_open_file(f)
            if v is not None and not v.close():
                return

            send2trash.send2trash(f)

    def is_visible(self, files):
        return len(files) > 0


class NewFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.show_input_panel("Folder Name:", "", functools.partial(self.on_done, dirs[0]), None, None)

    def on_done(self, dir, name):
        os.makedirs(os.path.join(dir, name), 0o775)

    def is_visible(self, dirs):
        return len(dirs) == 1


class DeleteFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):

        if len(dirs) == 1:
            message = "Delete Folder %s?" % dirs[0]
        else:
            message = "Delete %d Folders?" % len(dirs)

        if sublime.ok_cancel_dialog(message, "Delete"):
            import Default.send2trash as send2trash
            try:
                for d in dirs:
                    send2trash.send2trash(d)
            except:
                sublime.status_message("Unable to delete folder")

    def is_visible(self, dirs):
        return len(dirs) > 0


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
        self.window.run_command("open_dir", {"dir": branch, "file": leaf})

    def is_visible(self, files):
        return len(files) > 0


class FindInFolderCommand(sublime_plugin.WindowCommand):
    def run(self, dirs):
        self.window.run_command("show_panel", {"panel": "find_in_files", "where": ",".join(dirs)})

    def is_visible(self, dirs):
        return len(dirs) > 0
