import os
import sublime
import sublime_plugin


def advance_to_first_non_white_space_on_line(view, pt):
    while True:
        c = view.substr(pt)
        if c == " " or c == "\t":
            pt += 1
        else:
            break

    return pt


def has_non_white_space_on_line(view, pt):
    while True:
        c = view.substr(pt)
        if c == " " or c == "\t":
            pt += 1
        else:
            return c != "\n"


def build_comment_data(view, pt):
    shell_vars = view.meta_info("shellVariables", pt)
    if not shell_vars:
        return ([], [])

    # transform the list of dicts into a single dict
    all_vars = {}
    for v in shell_vars:
        if 'name' in v and 'value' in v:
            all_vars[v['name']] = v['value']

    line_comments = []
    block_comments = []

    # transform the dict into a single array of valid comments
    suffixes = [""] + ["_" + str(i) for i in range(1, 10)]
    for suffix in suffixes:
        start = all_vars.get("TM_COMMENT_START" + suffix)
        end = all_vars.get("TM_COMMENT_END" + suffix)
        disable_indent = all_vars.get("TM_COMMENT_DISABLE_INDENT" + suffix)

        if start and end:
            block_comments.append((start, end, disable_indent == 'yes'))
            block_comments.append((start.strip(), end.strip(), disable_indent == 'yes'))
        elif start:
            line_comments.append((start, disable_indent == 'yes'))
            line_comments.append((start.strip(), disable_indent == 'yes'))

    return (line_comments, block_comments)


def min_indent_lines(view, lines):
    tab_size = view.settings().get("tab_size", 4)

    # Find the minimum indentation across the lines, accounting for tab size
    min_indent = None
    for line in lines:
        indent = 0
        assert line.a <= line.b
        for pt in range(line.a, line.b):
            c = view.substr(pt)
            if c == " ":
                indent += 1
            elif c == "\t":
                indent += tab_size - (indent % tab_size)
            else:
                break

        if min_indent is None or indent < min_indent:
            min_indent = indent

    # Adjust line regions to start at the minimum indentation
    for line in lines:
        indent = 0
        for pt in range(line.a, line.b):
            c = view.substr(pt)
            if c == " ":
                next_indent = indent + 1
            elif c == "\t":
                next_indent = indent + tab_size - (indent % tab_size)
            else:
                break

            # Tabs may cause the indentation to go past the minimum. Take the
            # previous point instead.
            if next_indent > min_indent:
                line.a = pt
                break

            indent = next_indent
            if indent == min_indent:
                line.a = pt + 1
                break


class ToggleCommentCommand(sublime_plugin.TextCommand):
    def remove_block_comment(self, view, edit, region):
        scope = view.scope_name(region.begin())

        if region.end() > region.begin() + 1:
            end_scope = view.scope_name(region.end() - 1)
            # Find the common scope prefix. This results in correct behavior in
            # embedded-language situations.
            scope = os.path.commonprefix([scope, end_scope])

        index = scope.rfind(' comment.block.')
        if index == -1:
            return False

        selector = scope[:index + len(' comment.block')]

        whole_region = view.expand_to_scope(region.begin(), selector)

        if whole_region.end() < region.end():
            return False

        block_comments = build_comment_data(view, whole_region.begin())[1]

        for c in block_comments:
            (start, end, disable_indent) = c
            start_region = sublime.Region(whole_region.begin(), whole_region.begin() + len(start))
            end_region = sublime.Region(whole_region.end() - len(end), whole_region.end())

            if view.substr(start_region) == start and view.substr(end_region) == end:
                # It's faster to erase the start region first
                view.erase(edit, start_region)

                end_region = sublime.Region(
                    end_region.begin() - start_region.size(),
                    end_region.end() - start_region.size())

                view.erase(edit, end_region)
                return True

        return False

    def remove_line_comment(self, view, edit, region):
        start_positions = [advance_to_first_non_white_space_on_line(
            view, r.begin()) for r in view.lines(region)]
        start_positions = list(filter(
            lambda p: has_non_white_space_on_line(view, p), start_positions))
        if len(start_positions) == 0:
            return False

        line_comments = build_comment_data(view, start_positions[0])[0]

        regions = []
        for pos in start_positions:
            found = False
            for (start, _) in line_comments:
                comment_region = sublime.Region(pos, pos + len(start))
                if view.substr(comment_region) == start:
                    found = True
                    regions.append(comment_region)
                    break
            if not found:
                return False

        for region in reversed(regions):
            view.erase(edit, region)

        return True

    def block_comment_region(self, view, edit, region, variant, enable_indent=False):
        comment_data = build_comment_data(view, region.begin())

        if region.end() > region.begin() + 1:
            if build_comment_data(self.view, region.end() - 1) != comment_data:
                return False

        if len(comment_data[1]) <= variant:
            return False

        (start, end, disable_indent) = comment_data[1][variant]

        if enable_indent and not disable_indent:
            min_indent_lines(view, [region])

        if region.empty():
            # Silly buggers to ensure the cursor doesn't end up after the end
            # comment token
            view.replace(edit, sublime.Region(region.end()), 'x')
            view.insert(edit, region.end() + 1, end)
            view.replace(edit, sublime.Region(region.end(), region.end() + 1), '')
            view.insert(edit, region.begin(), start)
        else:
            view.insert(edit, region.end(), end)
            view.insert(edit, region.begin(), start)

        return True

    def line_comment_region(self, view, edit, region, variant):
        lines = view.lines(region)

        # Remove any blank lines from consideration, they make getting the
        # comment start markers to line up challenging
        non_empty_lines = list(filter(
            lambda l: has_non_white_space_on_line(view, l.a), lines))

        # If all the lines are blank however, just comment away
        if len(non_empty_lines) != 0:
            lines = non_empty_lines

        comment_data = build_comment_data(view, lines[0].a)

        if len(comment_data[0]) <= variant:
            # When there's no line comments fall back on the block comment. Only
            # do this for single lines, otherwise we want to fall back on
            # block-comment behavior.
            if len(lines) == 1:
                line = lines[0]
                pt = advance_to_first_non_white_space_on_line(view, line.begin())
                if self.remove_block_comment(view, edit, sublime.Region(pt)):
                    return True

                if self.block_comment_region(view, edit, line, variant, True):
                    return True

            return False

        (start, disable_indent) = comment_data[0][variant]

        if not disable_indent:
            min_indent_lines(view, lines)

        for line in reversed(lines):
            view.insert(edit, line.begin(), start)

        return True

    def run(self, edit, block=False, variant=0):
        for region in self.view.sel():
            if self.remove_block_comment(self.view, edit, region):
                continue

            if self.remove_line_comment(self.view, edit, region):
                continue

            if block:
                if not self.block_comment_region(self.view, edit, region, variant):
                    self.line_comment_region(self.view, edit, region, variant)
            else:
                if not self.line_comment_region(self.view, edit, region, variant):
                    self.block_comment_region(self.view, edit, region, variant)
