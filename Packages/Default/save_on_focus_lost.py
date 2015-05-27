import sublime, sublime_plugin
import os.path

class SaveOnFocusLost(sublime_plugin.EventListener):
    def on_deactivated_async(self, view):
        # The check for os.path.exists ensures that deleted files won't be
        # resurrected
        fname = view.file_name()

        if (fname and view.is_dirty() and
                view.settings().get('save_on_focus_lost') == True and
                os.path.exists(fname)):
            view.run_command('save');
