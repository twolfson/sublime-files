import sublime_plugin


class EchoCommand(sublime_plugin.ApplicationCommand):
    def run(self, **kwargs):
        print(kwargs)
