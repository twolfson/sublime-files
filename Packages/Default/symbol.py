import sublime, sublime_plugin

def lookup_symbol(window, symbol):
    if len(symbol.strip()) < 3:
        return []

    index_locations = window.lookup_symbol_in_index(symbol)
    open_file_locations = window.lookup_symbol_in_open_files(symbol)

    def file_in_location_list(fname, locations):
        for l in locations:
            if l[0] == fname:
                return True
        return False;

    # Combine the two lists, overriding results in the index with results
    # from open files, while trying to preserve the order of the files in
    # the index.
    locations = []
    ofl_ignore = []
    for l in index_locations:
        if file_in_location_list(l[0], open_file_locations):
            if not file_in_location_list(l[0], ofl_ignore):
                for ofl in open_file_locations:
                    if l[0] == ofl[0]:
                        locations.append(ofl)
                        ofl_ignore.append(ofl)
        else:
            locations.append(l)

    for ofl in open_file_locations:
        if not file_in_location_list(ofl[0], ofl_ignore):
            locations.append(ofl)

    return locations

def symbol_at_point(view, pt):
    symbol = view.substr(view.expand_by_class(pt,
        sublime.CLASS_WORD_START | sublime.CLASS_WORD_END,
        "[]{}()<>:."))
    locations = lookup_symbol(view.window(), symbol)

    if len(locations) == 0:
        symbol = view.substr(view.word(pt))
        locations = lookup_symbol(view.window(), symbol)

    return symbol, locations

def navigate_to_symbol(view, symbol, locations):
    def open_location(window, l):
        fname, display_fname, rowcol = l
        row, col = rowcol

        v = window.open_file(fname + ":" + str(row) + ":" + str(col),
            sublime.ENCODED_POSITION | sublime.FORCE_GROUP)

    def select_entry(window, locations, idx, orig_view, orig_sel):
        if idx >= 0:
            open_location(window, locations[idx])
        else:
            if orig_view:
                orig_view.sel().clear()
                orig_view.sel().add_all(orig_sel)
                window.focus_view(orig_view)
                orig_view.show(orig_sel[0])

    def highlight_entry(window, locations, idx):
        fname, display_fname, rowcol = locations[idx]
        row, col = rowcol

        window.open_file(fname + ":" + str(row) + ":" + str(col),
            group = window.active_group(),
            flags = sublime.TRANSIENT | sublime.ENCODED_POSITION | sublime.FORCE_GROUP)

    def format_location(l):
        fname, display_fname, rowcol = l
        row, col = rowcol

        return display_fname + ":" + str(row)

    orig_sel = None
    if view:
        orig_sel = [r for r in view.sel()]

    if len(locations) == 0:
        sublime.status_message("Unable to find " + symbol)
    elif len(locations) == 1:
        open_location(view.window(), locations[0])
    else:
        window = view.window()
        window.show_quick_panel(
            items = [format_location(l) for l in locations],
            on_select = lambda x: select_entry(window, locations, x, view, orig_sel),
            on_highlight = lambda x: highlight_entry(window, locations, x),
            flags = sublime.KEEP_OPEN_ON_FOCUS_LOST)

class GotoDefinition(sublime_plugin.WindowCommand):
    def run(self, symbol = None):
        v = self.window.active_view()

        if not symbol and not v:
            return

        if not symbol:
            pt = v.sel()[0]

            symbol, locations = symbol_at_point(v, pt)
        else:
            locations = lookup_symbol(self.window, symbol)

        navigate_to_symbol(v, symbol, locations)

class ContextGotoDefinitionCommand(sublime_plugin.TextCommand):
    def run(self, edit, event):
        pt = self.view.window_to_text((event["x"], event["y"]))

        symbol, locations = symbol_at_point(self.view, pt)

        navigate_to_symbol(self.view, symbol, locations)

    def is_visible(self, event):
        pt = self.view.window_to_text((event["x"], event["y"]))
        symbol, locations = symbol_at_point(self.view, pt)

        return len(locations) > 0

    def want_event(self):
        return True
