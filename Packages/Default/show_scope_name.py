import sublime
import sublime_plugin


def copy(view, text):
    sublime.set_clipboard(text)
    view.hide_popup()
    sublime.status_message('Scope name copied to clipboard')


class ShowScopeNameCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        scope = self.view.scope_name(self.view.sel()[-1].b)

        html = """
            <body id=show-scope>
                <style>
                    p {
                        margin-top: 0;
                    }
                    a {
                        font-family: system;
                        font-size: 1.05rem;
                    }
                </style>
                <p>%s</p>
                <a href="%s">Copy</a>
            </body>
        """ % (scope.replace(' ', '<br>'), scope.rstrip())

        self.view.show_popup(html, max_width=512, on_navigate=lambda x: copy(self.view, x))
