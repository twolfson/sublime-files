import sublime, sublime_plugin
import re

class ClipboardHistory():
    """
    Stores the current paste history
    """

    LIST_LIMIT = 15

    def __init__(self):
        self.storage = []

    def push_text(self, text):
        if not text:
            return

        DISPLAY_LEN = 45

        # create a display text out of the text
        display_text = re.sub(r'[\n]', '', text)
        # trim all starting space/tabs
        display_text = re.sub(r'^[\t\s]+', '', display_text)
        display_text = (display_text[:DISPLAY_LEN] + '...') if len(display_text) > DISPLAY_LEN else display_text

        self.del_duplicate(text)
        self.storage.insert(0, (display_text, text));

        if len(self.storage) > self.LIST_LIMIT:
            del self.storage[self.LIST_LIMIT:]

    def get(self):
        return self.storage

    def del_duplicate(self, text):
        # remove all dups
        self.storage = [s for s in self.storage if s[1] != text]

    def empty(self):
        return len(self.storage) == 0


g_clipboard_history = ClipboardHistory()

class ClipboardHistoryUpdater(sublime_plugin.EventListener):
    """
    Listens on the sublime text events and push the clipboard content into the
    ClipboardHistory object
    """

    def on_post_text_command(self, view, name, args):
        if view.settings().get('is_widget'):
            return

        if name == 'copy' or name == 'cut':
            g_clipboard_history.push_text(sublime.get_clipboard())

class PasteFromHistoryCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.settings().get('is_widget'):
            return

        # provide paste choices
        paste_list = g_clipboard_history.get()
        keys = [x[0] for x in paste_list]
        self.view.show_popup_menu(
            keys,
            lambda choice_index : self.paste_choice(choice_index))

    def is_enabled(self):
        return not g_clipboard_history.empty()

    def paste_choice(self, choice_index):
        if choice_index == -1:
            return
        # use normal paste command
        text = g_clipboard_history.get()[choice_index][1]

        # rotate to top
        g_clipboard_history.push_text(text)

        sublime.set_clipboard(text)
        self.view.run_command("paste");

