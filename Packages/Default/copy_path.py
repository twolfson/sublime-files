import sublime
import sublime_plugin


class CopyPathCommand(sublime_plugin.WindowCommand):
    def run(self):
        sheet = self.window.active_sheet()

        if sheet and len(sheet.file_name()) > 0:
            sublime.set_clipboard(sheet.file_name())
            sublime.status_message("Copied file path")

    def is_enabled(self):
        sheet = self.window.active_sheet()

        return sheet and sheet.file_name() is not None and len(sheet.file_name()) > 0
