import sublime_plugin


class TrimTrailingWhiteSpaceCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        trailing_white_space = self.view.find_all("[\t ]+$")
        trailing_white_space.reverse()
        for r in trailing_white_space:
            self.view.erase(edit, r)


class TrimTrailingWhiteSpace(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if view.settings().get("trim_trailing_white_space_on_save") is True:
            view.run_command("trim_trailing_white_space")


class EnsureNewlineAtEofCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        if self.view.size() > 0 and self.view.substr(self.view.size() - 1) != '\n':
            self.view.insert(edit, self.view.size(), "\n")


class EnsureNewlineAtEof(sublime_plugin.EventListener):
    def on_pre_save(self, view):
        if view.settings().get("ensure_newline_at_eof_on_save") is True:
            if view.size() > 0 and view.substr(view.size() - 1) != '\n':
                view.run_command("ensure_newline_at_eof")
