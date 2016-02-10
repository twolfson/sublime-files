import sublime
import sublime_plugin
import sublime_api

class ProfileSyntaxDefinitionCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):

        view = self.window.active_view()
        if not view:
            sublime.error_message("Syntax performance tests can only be run when a buffer is open")
            return

        if not hasattr(self, 'output_view'):
            # Try not to call get_output_panel until the regexes are assigned
            self.output_view = self.window.create_output_panel("exec")

        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)

        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel("exec")

        show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
        if show_panel_on_build:
            self.window.run_command("show_panel", {"panel": "output.exec"})

        source = view.substr(sublime.Region(0, view.size()))
        syntax = view.settings().get("syntax")

        total = 0.0
        for _ in range(0, 10):
            total += sublime_api.profile_syntax_definition(source, syntax)
        avg = total / 10.0

        output = 'Syntax "{}" took an average of {:,.1f}ms over 10 runs\n[Finished]'.format(syntax, avg * 1000.0)

        self.output_view.run_command('append', {'characters': output, 'force': True, 'scroll_to_end': True})
