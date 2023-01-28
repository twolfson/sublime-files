import sublime
import sublime_plugin


def fold_region_from_indent(view, r):
    if view.substr(r.b - 1) != '\n':
        return sublime.Region(r.a - 1, r.b)
    else:
        return sublime.Region(r.a - 1, r.b - 1)


class FoldUnfoldCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        new_sel = []
        for s in self.view.sel():
            r = s
            empty_region = r.empty()
            if empty_region:
                r = sublime.Region(r.a - 1, r.a + 1)

            unfolded = self.view.unfold(r)
            if len(unfolded) == 0:
                self.view.fold(s)
            elif empty_region:
                for r in unfolded:
                    new_sel.append(r)

        if len(new_sel) > 0:
            self.view.sel().clear()
            for r in new_sel:
                self.view.sel().add(r)
