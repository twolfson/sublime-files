import sublime, sublime_plugin

def next_line(view, pt):
    return view.line(pt).b + 1

def prev_line(view, pt):
    return view.line(pt).a - 1

def is_ws(str):
    for ch in str:
        if ch != ' ' and ch != '\t':
            return False
    return True

def indented_block(view, r):
    if r.empty():
        if r.a == view.size():
            return False

        nl = next_line(view, r.a)
        nr = view.indented_region(nl)
        if nr.a < nl:
            nr.a = nl

        this_indent = view.indentation_level(r.a)
        next_indent = view.indentation_level(nl)

        ok = False

        if this_indent + 1 == next_indent:
            ok = True

        if not ok:
            prev_indent = view.indentation_level(prev_line(view, r.a))

            # Mostly handle the care where the user has just pressed enter, and the
            # auto indent will update the indentation to something that will trigger
            # the block behavior when { is pressed
            line_str = view.substr(view.line(r.a))
            if is_ws(line_str) and len(view.get_regions("autows")) > 0:
                if prev_indent + 1 == this_indent and this_indent == next_indent:
                    ok = True

        if ok:
            # ensure that every line of nr is indented more than nl
            l = next_line(view, nl)
            while l < nr.end():
                if view.indentation_level(l) == next_indent:
                    return False
                l = next_line(view, l)
            return True

    return False

class BlockContext(sublime_plugin.EventListener):
    def on_query_context(self, view, key, operator, operand, match_all):
        if key == "indented_block":
            is_all = True
            is_any = False

            if operator != sublime.OP_EQUAL and operator != sublime.OP_NOT_EQUAL:
                return False

            for r in view.sel():
                if operator == sublime.OP_EQUAL:
                    b = (operand == indented_block(view, r))
                else:
                    b = (operand != indented_block(view, r))

                if b:
                    is_any = True
                else:
                    is_all = False

            if match_all:
                return is_all
            else:
                return is_any

        return None


class WrapBlockCommand(sublime_plugin.TextCommand):
    def run(self, edit, begin, end):

        self.view.run_command('insert', {'characters': begin})

        regions = reversed([s for s in self.view.sel()])
        for r in regions:
            if r.empty():
                nl = next_line(self.view, r.a)
                nr = self.view.indented_region(nl)

                begin_line = self.view.substr(self.view.line(r.a))

                ws = ""
                for ch in begin_line:
                    if ch == ' ' or ch == '\t':
                        ws += ch
                    else:
                        break;

                self.view.insert(edit, nr.end(), ws + end + "\n")

