import os
import re

import sublime
import sublime_api
import sublime_plugin


PACKAGES_FILE_REGEX = r'^Packages/(..[^:]*):([0-9]+):?([0-9]+)?:? (.*)$'


class RunSyntaxTestsCommand(sublime_plugin.WindowCommand):
    def run(self, find_all=False, **kwargs):

        if not hasattr(self, 'output_view'):
            # Try not to call get_output_panel until the regexes are assigned
            self.output_view = self.window.create_output_panel('exec')

        settings = self.output_view.settings()
        settings.set('result_file_regex', PACKAGES_FILE_REGEX)
        settings.set('result_base_dir', sublime.packages_path())
        settings.set('word_wrap', True)
        settings.set('line_numbers', False)
        settings.set('gutter', False)
        settings.set('scroll_past_end', False)

        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel('exec')

        if not find_all:
            relative_path = package_relative_path(self.window.active_view())
            if not relative_path:
                return

            file_name = os.path.basename(relative_path)

            if is_syntax(relative_path):
                tests = []
                for t in sublime.find_resources('syntax_test*'):
                    first_line = sublime.load_resource(t).splitlines()[0]
                    match = re.match('^.*SYNTAX TEST "(.*?)"', first_line)
                    if not match:
                        continue
                    syntax = match.group(1)
                    if syntax == relative_path or syntax == file_name:
                        tests.append(t)
            elif file_name.startswith('syntax_test'):
                tests = [relative_path]
            else:
                sublime.error_message(
                    'The current file is not a  *.sublime-syntax, *.tmLanguage '
                    'or syntax_test* file')
                return
        else:
            tests = sublime.find_resources('syntax_test*')

        show_panel_on_build(self.window)

        total_assertions = 0
        failed_assertions = 0

        for t in tests:
            assertions, test_output_lines = sublime_api.run_syntax_test(t)
            total_assertions += assertions
            if len(test_output_lines) > 0:
                failed_assertions += len(test_output_lines)
                for line in test_output_lines:
                    append(self.output_view, line + '\n')

        if failed_assertions > 0:
            message = 'FAILED: {} of {} assertions in {} files failed\n'
            params = (failed_assertions, total_assertions, len(tests))
        else:
            message = 'Success: {} assertions in {} files passed\n'
            params = (total_assertions, len(tests))

        append(self.output_view, message.format(*params))
        append(self.output_view, '[Finished]')

    def in_dir(self, folder, path):
        if not folder.endswith(os.sep):
            folder += os.sep
        return path.startswith(folder)


class ProfileSyntaxDefinitionCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):

        view = self.window.active_view()
        if not view:
            sublime.error_message('Syntax performance tests can only be run when a buffer is open')
            return

        if not hasattr(self, 'output_view'):
            # Try not to call get_output_panel until the regexes are assigned
            self.output_view = self.window.create_output_panel('exec')

        self.output_view.settings().set('line_numbers', False)
        self.output_view.settings().set('gutter', False)
        self.output_view.settings().set('scroll_past_end', False)

        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel('exec')

        show_panel_on_build(self.window)

        source = view.substr(sublime.Region(0, view.size()))
        syntax = view.settings().get('syntax')

        total = 0.0
        for _ in range(0, 10):
            total += sublime_api.profile_syntax_definition(source, syntax)
        avg = total / 10.0

        output = 'Syntax "{}" took an average of {:,.1f}ms over 10 runs\n' \
            '[Finished]'
        append(self.output_view, output.format(syntax, avg * 1000.0))


class SyntaxDefinitionCompatibilityCommand(sublime_plugin.WindowCommand):
    def run(self, **kwargs):

        view = self.window.active_view()
        if not view or not view.file_name().endswith('.sublime-syntax'):
            sublime.error_message(
                'Syntax compatibility tests can only be run when a '
                '.sublime-syntax file is open')
            return

        if not hasattr(self, 'output_view'):
            # Try not to call get_output_panel until the regexes are assigned
            self.output_view = self.window.create_output_panel('exec')

        settings = self.output_view.settings()
        settings.set('result_file_regex', PACKAGES_FILE_REGEX)
        settings.set('result_base_dir', sublime.packages_path())
        settings.set('word_wrap', True)
        settings.set('line_numbers', False)
        settings.set('gutter', False)
        settings.set('scroll_past_end', False)

        # Call create_output_panel a second time after assigning the above
        # settings, so that it'll be picked up as a result buffer
        self.window.create_output_panel('exec')

        relative_path = package_relative_path(view)
        if not relative_path:
            return

        show_panel_on_build(self.window)

        patterns = sublime_api.incompatible_syntax_patterns(relative_path)

        num = len(patterns)

        if num > 0:
            line_pattern = '{}:{}:{}: {}\n'
            for pattern in sorted(patterns, key=lambda p: p[0]):
                value_line, value_col = pattern[0]
                regex_line, regex_col = pattern[1]

                value_begin = view.text_point(value_line, value_col)
                next_char = view.substr(value_begin)
                while next_char == ' ':
                    value_col += 1
                    value_begin = view.text_point(value_line, value_col)
                    next_char = view.substr(value_begin)

                line = value_line + regex_line
                col = value_col + regex_col

                # Reconstruct the file cursor position by consuming YAML
                # string encoding

                # Quoted strings
                if next_char in {'\'', '"'}:
                    col += 1

                    chunk_begin = value_begin + 1
                    chunk_end = chunk_begin + regex_col
                    escaped_quotes = self.count_escapes(next_char, view, chunk_begin, chunk_end)

                    while escaped_quotes:
                        col += escaped_quotes
                        chunk_begin = chunk_end
                        chunk_end += escaped_quotes
                        escaped_quotes = self.count_escapes(next_char, view, chunk_begin, chunk_end)

                # Block strings
                elif next_char == '|':
                    line += 1
                    # Figure out the negative indent of the first line
                    value_point = view.text_point(value_line + 1, 0)
                    value_line = view.substr(view.line(value_point))
                    indent_size = len(value_line) - len(value_line.lstrip())
                    col = indent_size + regex_col

                # Folded strings
                elif next_char == '>':
                    def get_line(view, line_num):
                        point = view.text_point(line_num, 0)
                        return view.substr(view.line(point))

                    line += 1
                    raw_line = get_line(view, line)
                    stripped_line = raw_line.lstrip()
                    stripped_len = len(stripped_line)
                    indent_size = len(raw_line) - stripped_len
                    consumed = 0

                    while consumed + stripped_len + 1 <= regex_col:
                        consumed += stripped_len + 1
                        line += 1
                        raw_line = get_line(view, line)
                        stripped_line = raw_line.lstrip()
                        stripped_len = len(stripped_line)
                        indent_size = len(raw_line) - stripped_len

                    col = indent_size + (regex_col - consumed)

                append(self.output_view, line_pattern.format(relative_path, line + 1, col + 1, pattern[2]))

            message = 'FAILED: {} pattern{} in "{}" are incompatible with the new regex engine\n'
            s = 's' if num > 1 else ''
            params = (num, s, relative_path)

        else:
            message = 'Success: all patterns in "{}" are compatible with the new regex engine\n'
            params = (relative_path,)

        append(self.output_view, message.format(*params))
        append(self.output_view, '[Finished]')

    def count_escapes(self, quote, view, begin, end):
        chunk = view.substr(sublime.Region(begin, end))
        if quote == '\'':
            return chunk.count('\'\'')
        return len(re.findall('\\\\.', chunk))


def is_syntax(path):
    return path.endswith('.sublime-syntax') or path.endswith('.tmLanguage')


def package_relative_path(view):
    def show_error():
        sublime.error_message(
            'The current file can not be used for testing since it is not '
            'loaded by Sublime Text.\n\nThis is usually caused by a file not '
            'located in, or symlinked to, the Packages folder.')

    if not view:
        show_error()
        return None

    def os_to_resource_path(p):
        if p and os.name == 'nt':
            p = p.replace('\\', '/')
        return p

    path = None
    file_name = None
    relative_path = None

    packages_path = sublime.packages_path()
    data_dir = os.path.dirname(packages_path) + os.sep

    path = view.file_name()
    file_name = os.path.basename(path)
    if path.startswith(data_dir):
        relative_path = os_to_resource_path('Packages' + path[len(packages_path):])

    else:
        # Detect symlinked files that are opened from outside the Packages dir
        prefix = os.path.dirname(path)
        suffix = file_name
        while not prefix.endswith(os.sep):
            if os.path.exists(os.path.join(packages_path, suffix)):
                relative_path = os_to_resource_path(os.path.join('Packages', suffix))
                break
            prefix, tail = os.path.split(prefix)
            suffix = os.path.join(tail, suffix)

        # If we found what we think is a match, check and make sure the files
        # are actually the same. Otherwise it may just be a checked-out version
        # of the Packages repository.
        if relative_path:
            try:
                loader_version = sublime.load_resource(relative_path)
            except IOError:
                relative_path = None
            else:
                with open(path, 'r', encoding='utf-8', newline='') as f:
                    fs_version = f.read()
                if fs_version != loader_version:
                    relative_path = None

    if not relative_path:
        show_error()

    return relative_path


def show_panel_on_build(window):
    if sublime.load_settings('Preferences.sublime-settings').get(
            'show_panel_on_build', True):
        window.run_command('show_panel', {'panel': 'output.exec'})


def append(panel, output):
    panel.run_command('append', {'characters': output, 'force': True, 'scroll_to_end': True})
