import re
import webbrowser

import sublime_plugin


rex = re.compile(
    r'''(?x)
    \b(?:
        https?://(?:(?:[a-zA-Z0-9\-_]+(?:\.[a-zA-Z0-9\-._]+)+)|localhost)|  # http://
        www\.[a-zA-Z0-9\-_]+(?:\.[a-zA-Z0-9\-._]+)+                         # www.
    )
    /?[a-zA-Z0-9\-._?,!'(){}\[\]/+&@%$#=:"|~;]*                             # url path and query string
    [a-zA-Z0-9\-_~:/#@$*+=]                                                 # allowed end chars
    ''')


class OpenContextUrlCommand(sublime_plugin.TextCommand):
    def run(self, edit, event):
        url = self.find_url(event)
        webbrowser.open_new_tab(url)

    def is_visible(self, event):
        return self.find_url(event) is not None

    def find_url(self, event):
        pt = self.view.window_to_text((event["x"], event["y"]))
        line = self.view.line(pt)

        line.a = max(line.a, pt - 1024)
        line.b = min(line.b, pt + 1024)

        text = self.view.substr(line)

        it = rex.finditer(text)

        for match in it:
            if match.start() <= (pt - line.a) and match.end() >= (pt - line.a):
                url = text[match.start():match.end()]
                if url[0:3] == "www":
                    return "http://" + url
                else:
                    return url

        return None

    def description(self, event):
        url = self.find_url(event)
        if len(url) > 64:
            url = url[0:64] + "..."
        return "Open " + url

    def want_event(self):
        return True
