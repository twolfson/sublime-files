import sys

import sublime
import sublime_plugin


class PrimaryJChangedCommand(sublime_plugin.WindowCommand):
    def run(self):
        primary = 'Cmd' if sys.platform == 'darwin' else 'Ctrl'

        sublime.message_dialog(
            "Key Binding Changed\n"
            "\n"
            "The key binding for Join Lines has changed to "
            f"{primary}+Shift+J.\n"
            "\n"
            f"The binding was changed to open up {primary}+J to be used as "
            "the first key press for various new key bindings, such as "
            "Unselect to Left, Unselect to Right, Select to Left and "
            "Select to Right."
        )

    def name(self):
        return "primary_j_changed"
