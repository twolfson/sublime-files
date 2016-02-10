import sublime
import sublime_plugin
import sublime_api
import os
import re

class RunSyntaxTestsCommand(sublime_plugin.WindowCommand):
    def run(self,
        file_regex = "",
        line_regex = "",
        working_dir = "",
        quiet = False,
        word_wrap = True,
        syntax = "Packages/Text/Plain text.tmLanguage",
        find_all = False,
        **kwargs):

        if not hasattr(self, 'output_view'):
            # Try not to call get_output_panel until the regexes are assigned
            self.output_view = self.window.create_output_panel("exec")

        # Default the to the current files directory if no working directory was given
        if (working_dir == "" and self.window.active_view()
                        and self.window.active_view().file_name()):
            working_dir = os.path.dirname(self.window.active_view().file_name())

        self.output_view.settings().set("result_file_regex", file_regex)
        self.output_view.settings().set("result_line_regex", line_regex)
        self.output_view.settings().set("result_base_dir", working_dir)
        self.output_view.settings().set("word_wrap", word_wrap)
        self.output_view.settings().set("line_numbers", False)
        self.output_view.settings().set("gutter", False)
        self.output_view.settings().set("scroll_past_end", False)
        self.output_view.assign_syntax(syntax)

        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel("exec")

        tests = sublime.find_resources("syntax_test*")
        if not find_all:
            path = None
            file_name = None
            relative_path = None

            packages_path = sublime.packages_path()
            data_dir = os.path.dirname(packages_path) + os.sep

            view = self.window.active_view()
            if view:
                path = view.file_name()
                file_name = os.path.basename(path)
                if path.startswith(data_dir):
                    relative_path = "Packages" + path[len(packages_path):]

                # Detect symlinked files that are opened from outside of the Packages dir
                else:
                    prefix = os.path.dirname(path)
                    suffix = file_name
                    while not prefix.endswith(os.sep):
                        if os.path.exists(os.path.join(packages_path, suffix)):
                            relative_path = os.path.join("Packages", suffix)
                            break
                        prefix, tail = os.path.split(prefix)
                        suffix = os.path.join(tail, suffix)

            if relative_path and os.name == 'nt':
                relative_path = relative_path.replace('\\', '/')

            is_syntax = path and path.endswith('.sublime-syntax') or path.endswith('.tmLanguage')

            if is_syntax:
                new_tests = []
                for t in tests:
                    first_line = sublime.load_resource(t).splitlines()[0]
                    match = re.match('^.*SYNTAX TEST "(.*?)"', first_line)
                    if match:
                        syntax_path = match.group(1)
                        if syntax_path == relative_path or syntax_path == file_name:
                            new_tests.append(t)
                tests = new_tests
            elif relative_path and file_name.startswith('syntax_test'):
                tests = [relative_path]
            else:
                sublime.error_message("The current file is not a *.sublime-syntax, *.tmLanguage or syntax_test* file")
                return

        show_panel_on_build = sublime.load_settings("Preferences.sublime-settings").get("show_panel_on_build", True)
        if show_panel_on_build:
            self.window.run_command("show_panel", {"panel": "output.exec"})

        output = ""
        total_assertions = 0
        failed_assertions = 0

        for t in tests:
            assertions, test_output_lines = sublime_api.run_syntax_test(t)
            total_assertions += assertions
            if len(test_output_lines) > 0:
                failed_assertions += len(test_output_lines)
                for line in test_output_lines:
                    output += line + "\n"

        self.append_string(output)

        if failed_assertions > 0:
            self.append_string(
                "FAILED: %d of %d assertions in %d files failed\n" %
                (failed_assertions, total_assertions, len(tests))
            )
        else:
            self.append_string(
                "Success: %d assertions in %s files passed\n" %
                (total_assertions, len(tests))
            )

        self.append_string("[Finished]")

    def append_string(self, str):
        self.output_view.run_command('append', {'characters': str, 'force': True, 'scroll_to_end': True})

    def in_dir(self, folder, path):
        if not folder.endswith(os.sep):
            folder += os.sep
        return path.startswith(folder)
