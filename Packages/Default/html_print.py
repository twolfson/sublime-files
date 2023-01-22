import sublime_plugin
import tempfile
import pathlib
import webbrowser


class HtmlPrintCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view

        html = view.export_to_html(enclosing_tags=True, font_size=False)

        with tempfile.NamedTemporaryFile('w', suffix=".html", encoding='utf-8', delete=False) as f:
            f.write("<html><head><meta charset=\"UTF-8\"></head><body>")
            f.write(html)
            f.write('<script>window.print()</script></body></html>')

        url = pathlib.Path(f.name).as_uri()
        controller = webbrowser.get(using=view.settings().get('print_using_browser'))
        controller.open_new_tab(url)
