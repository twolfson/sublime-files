import sublime_plugin


class QuickPanelCommand(sublime_plugin.WindowCommand):
    def select_item(self, items, idx):
        if idx >= 0:
            self.window.run_command(items[idx]["command"], items[idx]["args"])

    def run(self, items):
        self.window.show_quick_panel(
            items=[x["caption"] for x in items],
            on_select=lambda idx: self.select_item(items, idx))
