import os.path
import platform

import sublime
import sublime_plugin


def compare_extension(extension, fname):
    if platform.system() == 'Windows' or platform.system() == 'Darwin':
        extension = extension.lower()
        fname = fname.lower()

    return fname.lower().endswith('.' + extension.lower())


class SwitchFileCommand(sublime_plugin.WindowCommand):
    def run(self, extensions=[], side_by_side=False, event=None):
        if not self.window.active_view():
            return

        fname = self.window.active_view().file_name()
        if not fname:
            return

        if event and 'shift' in event.get('modifier_keys', {}):
            side_by_side = True

        replace_mru = False
        if len(self.window.selected_sheets()) > 1 \
                and not side_by_side:
            replace_mru = True

        base = os.path.splitext(fname)[0]

        start = 0
        count = len(extensions)

        if '.' in fname:
            # Extensions can be overlapping, like "ts" and "spec.ts". So instead
            # of finding the first matching extension we find the longest.
            ext_len = 0

            for i in range(0, len(extensions)):
                if compare_extension(extensions[i], fname) and len(extensions[i]) > ext_len:
                    start = i + 1
                    count -= 1
                    ext_len = len(extensions[i])
                    base = fname[:-ext_len - 1]

        for i in range(0, count):
            idx = (start + i) % len(extensions)

            new_path = base + '.' + extensions[idx]

            if os.path.exists(new_path):
                flags = sublime.FORCE_GROUP

                if side_by_side:
                    flags |= sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT
                elif replace_mru:
                    flags |= sublime.REPLACE_MRU | sublime.SEMI_TRANSIENT

                self.window.open_file(new_path, flags=flags)
                break

    def want_event(self):
        return True
