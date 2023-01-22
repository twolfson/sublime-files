import os

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
        for i, frame in enumerate(reversed(stack)):
            digits = '%s' % (i + 1)
            digits_len = max(len(digits), digits_len)
            nums = '<span class=nums>%s.</span>' % digits

            if frame.context_name.startswith("anonymous context "):
                context_name = '<em>%s</em>' % frame.context_name
            else:
                context_name = frame.context_name
            ctx = '<span class=context>%s</span>' % context_name

            resource_path = frame.source_file
            display_path = os.path.splitext(frame.source_file)[0]
            if resource_path.startswith('Packages/'):
                resource_path = '${packages}/' + resource_path[9:]
                display_path = display_path[9:]

            if frame.source_location[0] > 0:
                href = '%s:%d:%d' % (resource_path, *frame.source_location)
                location = '%s:%d:%d' % (display_path, *frame.source_location)
            else:
                href = resource_path
                location = display_path
            link = '<a href="o:%s">%s</a>' % (href, location)

            if backtrace:
                backtrace += '\n'
            backtrace += '<div>%s%s%s</div>' % (nums, ctx, link)

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
                <h1>Scope Name <a href="c:%s">Copy</a></h1>
                <p>%s</p>
                <h1>Context Backtrace</h1>
                %s
            </body>
        """ % (digits_len, scope, scope_list, backtrace)

        self.view.show_popup(html, max_width=512, max_height=512, on_navigate=self.on_navigate)

    def on_navigate(self, link):
        if link.startswith('o:'):
            self.view.window().run_command('open_file', {'file': link[2:], 'encoded_position': True})
        else:
            copy(self.view, link[2:])
