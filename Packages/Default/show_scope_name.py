import sublime
import sublime_plugin


def copy(view, text):
    sublime.set_clipboard(text)
    view.hide_popup()
    sublime.status_message('Scope name copied to clipboard')


class ShowScopeNameCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        scope = self.view.scope_name(self.view.sel()[-1].b).rstrip()
        scope_list = scope.replace(' ', '<br>')

        stack = self.view.context_backtrace(self.view.sel()[-1].b)

        backtrace = ''
        digits_len = 1
        for i, ctx in enumerate(reversed(stack)):
            digits = '%s' % (i + 1)
            digits_len = max(len(digits), digits_len)
            nums = '<span class=nums>%s.</span>' % digits

            if ctx.startswith("anonymous context "):
                ctx = '<em>%s</em>' % ctx
            ctx = '<span class=context>%s</span>' % ctx

            if backtrace:
                backtrace += '\n'
            backtrace += '<div>%s%s</div>' % (nums, ctx)

        html = """
            <body id=show-scope>
                <style>
                    h1 {
                        font-size: 1.1rem;
                        font-weight: 500;
                        margin: 0 0 0.5em 0;
                        font-family: system;
                    }
                    p {
                        margin-top: 0;
                    }
                    a {
                        font-weight: normal;
                        font-style: italic;
                        padding-left: 1em;
                        font-size: 1.0rem;
                    }
                    span.nums {
                        display: inline-block;
                        text-align: right;
                        width: %dem;
                        color: color(var(--foreground) a(0.8))
                    }
                    span.context {
                        padding-left: 0.5em;
                    }
                </style>
                <h1>Scope Name <a href="%s">Copy</a></h1>
                <p>%s</p>
                <h1>Context Backtrace</h1>
                %s
            </body>
        """ % (digits_len, scope, scope_list, backtrace)

        self.view.show_popup(html, max_width=512, max_height=512, on_navigate=lambda x: copy(self.view, x))
