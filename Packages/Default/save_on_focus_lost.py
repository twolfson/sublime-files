import os.path

import sublime_plugin


class SaveOnFocusLost(sublime_plugin.EventListener):
    def on_deactivated_async(self, view):
        fname = view.file_name()

        if not fname or not view.is_dirty():
            return

        # The check for os.path.exists ensures that deleted files won't be resurrected
        if view.settings().get('save_on_focus_lost') is True and os.path.exists(fname):
            view.run_command('save')
