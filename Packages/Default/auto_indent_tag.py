import sublime_plugin


class AutoIndentTagCommand(sublime_plugin.TextCommand):

    def run(self, edit):
        view = self.view

        cursor = view.sel()[0].a
        cur_line = view.line(cursor)
        line_start = cur_line.a
        end = cursor - line_start
        preceeding = view.substr(cur_line)

        prev_tag = None
        next_tag = None

        while True:
            pos = preceeding.rfind('<', 0, end)

            # Not on the current line
            if pos == -1:
                # Abort at the beginning of the file
                if line_start == 0:
                    break
                prev_line = view.full_line(line_start - 1)
                line_start = prev_line.a
                preceeding = view.substr(prev_line)
                end = len(preceeding)
                continue

            point = line_start + pos

            if view.score_selector(point, 'punctuation.definition.tag.begin') > 0:
                # Skip the "<"
                point = self.skip_whitespace(point + 1)
                # If the preceeding tag is a close tag, no auto indent
                if view.substr(point) == '/':
                    break
                prev_tag = view.substr(view.extract_scope(point))
                break

            end = pos

        # Skip the "</"
        point = self.skip_whitespace(cursor + 2)
        next_tag = view.substr(view.extract_scope(point))

        if not prev_tag or not next_tag or prev_tag != next_tag:
            view.run_command('insert', {'characters': '\n'})
            return

        view.run_command('insert_snippet', {'contents': "\n\t$0\n"})

    def skip_whitespace(self, point):
        while self.view.substr(point) in {' ', '\t', '\n'}:
            point += 1
        return point
