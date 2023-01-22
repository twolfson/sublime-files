import sys
import html

import sublime
import sublime_plugin


def lookup_symbol(window, symbol, kind=sublime.KIND_ID_AMBIGUOUS):
    return window.symbol_locations(
        symbol,
        sublime.SYMBOL_SOURCE_ANY,
        sublime.SYMBOL_TYPE_DEFINITION,
        kind_id=kind
    )


def lookup_references(window, symbol):
    return window.symbol_locations(
        symbol,
        sublime.SYMBOL_SOURCE_ANY,
        sublime.SYMBOL_TYPE_REFERENCE
    )


def symbol_at_point(view, pt):
    symbol = view.substr(view.expand_by_class(pt, sublime.CLASS_WORD_START | sublime.CLASS_WORD_END, "[]{}()<>:."))
    locations = lookup_symbol(view.window(), symbol)

    if len(locations) == 0:
        symbol = view.substr(view.word(pt))
        locations = lookup_symbol(view.window(), symbol)

    return symbol, locations


def reference_at_point(view, pt):
    symbol = view.substr(view.expand_by_class(pt, sublime.CLASS_WORD_START | sublime.CLASS_WORD_END, "[]{}()<>:."))
    locations = lookup_references(view.window(), symbol)

    if len(locations) == 0:
        symbol = view.substr(view.word(pt))
        locations = lookup_references(view.window(), symbol)

    return symbol, locations


def open_location(window, l, side_by_side=False, replace=False, clear_to_right=False):
    flags = sublime.ENCODED_POSITION | sublime.FORCE_GROUP

    if side_by_side:
        flags |= sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT
        if clear_to_right:
            flags |= sublime.CLEAR_TO_RIGHT

    elif replace:
        flags |= sublime.REPLACE_MRU | sublime.SEMI_TRANSIENT
    window.open_file(l.path_encoded_position(), flags)


def format_location(l):
    return "%s:%d" % (html.escape(l.display_name), l.row)


def filter_current_symbol(view, point, symbol, locations):
    """
    Filter the point specified from the list of symbol locations. This
    results in a nicer user experience so the current symbol doesn't pop up
    when hovering over a class definition. We don't just skip all class and
    function definitions for the sake of languages that split the definition
    and implementation.
    """

    def match_view(path, view):
        fname = view.file_name()
        if fname is None:
            if path.startswith('<untitled '):
                path_view = view.window().find_open_file(path)
                return path_view and path_view.id() == view.id()
            return False
        return path == fname

    new_locations = []
    for l in locations:
        if match_view(l.path, view):
            symbol_begin_pt = view.text_point(l.row - 1, l.col)
            symbol_end_pt = symbol_begin_pt + len(symbol)
            if point >= symbol_begin_pt and point <= symbol_end_pt:
                continue
        new_locations.append(l)
    return new_locations


def scroll_to(row, col, view):
    pt = view.text_point(row - 1, col - 1)
    view.sel().clear()
    view.sel().add(sublime.Region(pt))
    view.show(pt, True)
    view.run_command('add_jump_record', {'selection': pt})


def navigate_to_symbol(
        view,
        symbol,
        locations,
        side_by_side=False,
        replace=False,
        clear_to_right=True,
        placeholder=None):
    open_file_states = {}
    highlighted_view = None
    prev_selected = view.window().selected_sheets()

    def file_name(view):
        name = view.file_name()
        if not name:
            name = '<untitled %d>' % view.buffer_id()
        return name

    def save_selections(view):
        if view.id() not in open_file_states:
            open_file_states[view.id()] = ([r for r in view.sel()], view.viewport_position())

    def restore_selections(view):
        if view.is_valid():
            selections, viewport_pos = open_file_states[view.id()]
            view.sel().clear()
            view.add_regions('jump_ignore_selection', selections)
            view.sel().add_all(selections)
            view.set_viewport_position(viewport_pos)

    def select_entry(window, locations, idx, event):

        nonlocal clear_to_right, side_by_side, replace

        if idx >= 0:
            for view_id in open_file_states:
                restore_view = sublime.View(view_id)
                if file_name(restore_view) != locations[idx].path:
                    restore_selections(restore_view)

            if side_by_side and clear_to_right:
                new_tab = True
                reopen_location = True
                if event:
                    if 'primary' in event['modifier_keys']:
                        reopen_location = False
                        new_tab = False
                    elif 'shift' in event['modifier_keys']:
                        new_tab = True
                    elif 'alt' in event['modifier_keys']:
                        replace = True
                        new_tab = False
                if reopen_location:
                    window.select_sheets(prev_selected)
                    window.focus_view(view)
                    if replace:
                        highlighted_view.close()
                    open_location(
                        window,
                        locations[idx],
                        new_tab,
                        replace,
                        False)

            # When in side-by-side mode, the file will already be open
            if not side_by_side:
                new_tab = False
                if event:
                    if 'primary' in event['modifier_keys']:
                        new_tab = True
                        clear_to_right = True
                    elif 'shift' in event['modifier_keys']:
                        new_tab = True
                    elif 'alt' in event['modifier_keys']:
                        replace = True
                open_location(
                    window,
                    locations[idx],
                    new_tab,
                    replace,
                    clear_to_right)
        else:
            for view_id in open_file_states:
                restore_selections(sublime.View(view_id))

            if event and event.get("key", None) and event["key"] == "escape":
                if view.is_valid():
                    window.focus_view(view)
                    view.show(view.sel()[0])
                # When in side-by-side mode close the current highlighted
                # sheet upon canceling if the sheet is semi-transient otherwise
                # deselect
                if side_by_side:
                    if highlighted_view.sheet().is_semi_transient():
                        highlighted_view.close()
                window.select_sheets(prev_selected)
            else:
                highlighted_sheet = highlighted_view.sheet()
                if highlighted_sheet.group() != window.active_group():
                    window.select_sheets(prev_selected)

                elif highlighted_sheet.is_transient():
                    window.promote_sheet(highlighted_sheet)

    def highlight_entry(window, locations, idx):
        nonlocal highlighted_view
        flags = sublime.ENCODED_POSITION | sublime.FORCE_GROUP
        if side_by_side:
            if not highlighted_view:
                # Adding to the selection is done relative to the focused view.
                # Don't focus original view if sheet is transient
                if view.is_valid() and not view.sheet().is_transient():
                    window.focus_view(view)

                flags |= sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT
                if clear_to_right:
                    flags |= sublime.CLEAR_TO_RIGHT

            else:
                if highlighted_view.is_valid():
                    if locations[idx].path == highlighted_view.file_name():
                        scroll_to(locations[idx].row, locations[idx].col, highlighted_view)
                    else:
                        # Replacing the MRU is done relative to the current highlighted sheet
                        window.focus_view(highlighted_view)
                        flags |= sublime.REPLACE_MRU | sublime.SEMI_TRANSIENT
                else:
                    # highlighted_view is no longer valid
                    flags |= sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT
        else:
            flags |= sublime.TRANSIENT

        highlighted_view = window.open_file(
            locations[idx].path_encoded_position(),
            group=window.active_group(),
            flags=flags)

    save_selections(view)

    if len(locations) == 0:
        sublime.status_message("Unable to find " + symbol)
    elif len(locations) == 1:
        open_location(view.window(), locations[0], side_by_side, replace)
    else:
        window = view.window()
        items = []
        for l in locations:
            items.append(sublime.QuickPanelItem(
                format_location(l),
                annotation=l.syntax,
                kind=l.kind
            ))
        window.show_quick_panel(
            items=items,
            on_select=lambda x, e: select_entry(window, locations, x, e),
            on_highlight=lambda x: highlight_entry(window, locations, x),
            flags=sublime.WANT_EVENT,
            placeholder=placeholder)


class GotoDefinition(sublime_plugin.WindowCommand):
    def run(
            self,
            event=None,
            symbol=None,
            kind=sublime.KIND_ID_AMBIGUOUS,
            side_by_side=False,
            replace=False,
            clear_to_right=False):
        v = self.window.active_view()

        if not symbol and not v:
            return

        if not symbol:
            # Ensure that events are processed correctly as goto_definition command can be run from a menubar item.
            # Event may contain "modifier_keys" but not "x" and "y", in which case fallback to current selection.
            if event and "x" in event and "y" in event:
                pt = v.window_to_text((event["x"], event["y"]))
                modifiers = event.get("modifier_keys", None)
                if modifiers:
                    if 'primary' in modifiers:
                        side_by_side = True
                        clear_to_right = True
            else:
                pt = v.sel()[0]

            symbol, locations = symbol_at_point(v, pt)
        else:
            locations = lookup_symbol(self.window, symbol, kind)

        navigate_to_symbol(v, symbol, locations, side_by_side, replace, clear_to_right, "Definitions of " + symbol)

    def is_visible(self, event=None, **args):
        if not event:
            return True
        v = self.window.active_view()

        if "x" in event and "y" in event:
            pt = v.window_to_text((event["x"], event["y"]))
            symbol, locations = symbol_at_point(v, pt)
            return len(locations) > 0

        return False

    def want_event(self):
        return True


def _sym_def_href(location, **kwargs):
    args = {
        "path": location.path_encoded_position(),
        "hide_popup": True
    }
    args.update(kwargs)
    return sublime.command_url("open_symbol_definition ", args)


class OpenSymbolDefinition(sublime_plugin.WindowCommand):
    def run(self,
            path,
            new_tab=False,
            hide_popup=False,
            keep_auto_complete_open=False,
            add_jump_point=-1,
            event=None,
            focus_view=None,
            clear_to_right=False):
        flags = sublime.ENCODED_POSITION | sublime.FORCE_GROUP

        active_view = self.window.active_view()
        active_group = self.window.active_group()
        selected_sheets = self.window.selected_sheets()

        prefocus = None
        prefocus_group = -1
        prefocus_index = -1
        if focus_view:
            prefocus = sublime.View(focus_view)
            prefocus_group, prefocus_index = self.window.get_view_index(prefocus)
            if prefocus_group != active_group:
                selected_sheets = self.window.selected_sheets_in_group(prefocus_group)

        if event:
            if 'primary' in event['modifier_keys']:
                new_tab = True
                clear_to_right = True
            elif 'shift' in event['modifier_keys']:
                new_tab = True
                clear_to_right = False

        view = self.window.active_view()
        if add_jump_point != -1:
            view.run_command('add_jump_record', {'selection': add_jump_point})
        if keep_auto_complete_open:
            view.preserve_auto_complete_on_focus_lost()

        # Make sure we use the current view if possible
        if not new_tab and path[:path.find(':')] == view.file_name() and event and 'alt' not in event['modifier_keys']:
            row, col = map(int, path[path.find(':') + 1:].split(':'))
            scroll_to(row, col, view)
        else:
            if event and 'alt' not in event['modifier_keys'] \
                    and len(selected_sheets) > 1 \
                    and not new_tab:
                if focus_view is not None and active_view.id() == focus_view:
                    prefocus = None
                flags |= sublime.REPLACE_MRU | sublime.SEMI_TRANSIENT
            elif event and 'alt' in event['modifier_keys'] and not new_tab:
                flags |= sublime.FORCE_CLONE

            if prefocus:
                self.window.focus_view(prefocus)

            if new_tab:
                flags |= sublime.ADD_TO_SELECTION | sublime.SEMI_TRANSIENT
                if clear_to_right:
                    flags |= sublime.CLEAR_TO_RIGHT

            self.window.open_file(path, flags, prefocus_group)

        if hide_popup:
            view.hide_popup()

    def want_event(self):
        return True


def _kind_class_name(kind_id):
    if kind_id == sublime.KIND_ID_KEYWORD:
        return "kind kind_keyword"
    if kind_id == sublime.KIND_ID_TYPE:
        return "kind kind_type"
    if kind_id == sublime.KIND_ID_FUNCTION:
        return "kind kind_function"
    if kind_id == sublime.KIND_ID_NAMESPACE:
        return "kind kind_namespace"
    if kind_id == sublime.KIND_ID_NAVIGATION:
        return "kind kind_navigation"
    if kind_id == sublime.KIND_ID_MARKUP:
        return "kind kind_markup"
    if kind_id == sublime.KIND_ID_VARIABLE:
        return "kind kind_variable"
    if kind_id == sublime.KIND_ID_SNIPPET:
        return "kind kind_snippet"
    return "kind kind_ambiguous"


def _popup_css():
    return """
        body {
            white-space: nowrap;
        }
        h1 {
            font-size: 1.1rem;
            font-weight: bold;
            margin: 0 0 0.5em 0;
        }
        h1 code {
            font-size: 0.9em;
            font-weight: normal;
            color: color(var(--foreground) a(0.7));
        }
        p {
            font-size: 1.05rem;
            margin: 0;
        }
        .icon {
            text-decoration: none;
            font-size: 1em;
        }
        a {
            line-height: 1.3;
        }
        span.syntax {
            color: color(var(--foreground) a(0.5));
            padding-left: 10px;
            font-style: italic;
            font-size: 0.9em;
        }
        span.kind {
            font-weight: bold;
            font-style: italic;
            width: 1.5rem;
            display: inline-block;
            text-align: center;
            font-family: system;
            line-height: 1.3;
            border-radius: 2px;
            position: relative;
            top: 1px;
            margin-right: 6px;
        }
        span.kind_ambiguous {
            display: none;
        }
        span.kind_keyword {
            background-color: color(var(--pinkish) a(0.2));
            color: var(--pinkish);
        }
        span.kind_type {
            background-color: color(var(--purplish) a(0.2));
            color: var(--purplish);
        }
        span.kind_function {
            background-color: color(var(--redish) a(0.2));
            color: var(--redish);
        }
        span.kind_namespace {
            background-color: color(var(--bluish) a(0.2));
            color: var(--bluish);
        }
        span.kind_navigation {
            background-color: color(var(--yellowish) a(0.2));
            color: var(--yellowish);
        }
        span.kind_markup {
            background-color: color(var(--orangish) a(0.2));
            color: var(--orangish);
        }
        span.kind_variable {
            background-color: color(var(--cyanish) a(0.2));
            color: var(--cyanish);
        }
        span.kind_snippet {
            background-color: color(var(--greenish) a(0.2));
            color: var(--greenish);
        }
    """


class AutoCompleteGotoDefinition(sublime_plugin.WindowCommand):
    def run(self, symbol, event=None):
        view = self.window.active_view()

        locations = lookup_symbol(self.window, symbol, sublime.KIND_ID_AMBIGUOUS)

        if len(locations) == 1:
            self.window.run_command(
                'open_symbol_definition',
                {
                    "path": locations[0].path_encoded_position(),
                    "new_tab": True,
                    "hide_popup": True,
                    "keep_auto_complete_open": True,
                    "event": event,
                }
            )
            return

        # If the user used the mouse, show a popup
        if event:
            link_markup = ('<span class="{class_name}" title="{name}">{letter}</span>'
                           '<a href="{href}">{location}</a>&nbsp;'
                           '<span class="syntax">{syntax}</span>')
            links = '<br>'.join(
                link_markup.format(
                    class_name=_kind_class_name(l.kind[0]),
                    letter=l.kind[1] if l.kind[1] else '&nbsp;',
                    name=l.kind[2] if l.kind[2] else '',
                    syntax=html.escape(l.syntax),
                    location=format_location(l),
                    href=_sym_def_href(l, new_tab=True, keep_auto_complete_open=True, focus_view=view.id()))
                for l in locations)

            plural = 's' if len(locations) != 1 else ''

            body = """
                <body id=show-definitions>
                    <style>
                        body {
                            font-family: system;
                            /*
                            Necessary due to COOPERATE_WITH_AUTO_COMPLETE
                            changing the margin to align with AC window
                            */
                            margin: 8px;
                        }
                        %s
                    </style>
                    <h1>Definition%s</h1>
                    <p>%s</p>
                </body>
            """ % (_popup_css(), plural, links)

            view.show_popup(
                body,
                flags=(sublime.HIDE_ON_MOUSE_MOVE_AWAY |
                       sublime.COOPERATE_WITH_AUTO_COMPLETE |
                       sublime.HIDE_ON_CHARACTER_EVENT),
                max_width=1024)
        else:
            view.preserve_auto_complete_on_focus_lost()
            navigate_to_symbol(view, symbol, locations, True, False, False, "Definitions of " + symbol)

    def is_visible(self, event=None, **args):
        if not event:
            return True

        v = self.window.active_view()

        pt = v.window_to_text((event["x"], event["y"]))
        symbol, locations = symbol_at_point(v, pt)

        return len(locations) > 0

    def want_event(self):
        return True


class GotoReference(sublime_plugin.WindowCommand):
    def run(self, symbol=None, side_by_side=False, replace=False, clear_to_right=False):
        v = self.window.active_view()

        if not symbol and not v:
            return

        if not symbol:
            pt = v.sel()[0]
            symbol, locations = reference_at_point(v, pt)
        else:
            locations = lookup_references(self.window, symbol)

        navigate_to_symbol(v, symbol, locations, side_by_side, replace, clear_to_right, "References to " + symbol)


class ShowDefinitions(sublime_plugin.EventListener):
    def on_hover(self, view, point, hover_zone):
        if not view.settings().get('show_definitions'):
            return

        ShowDefinitions.default_on_hover(view, point, hover_zone)

    def default_on_hover(view, point, hover_zone):
        if view.is_auto_complete_visible():
            return

        if hover_zone != sublime.HOVER_TEXT:
            return

        def score(scopes):
            return view.score_selector(point, scopes)

        # Limit where we show the hover popup
        if score('text.html') and not score('text.html source'):
            is_class = score('meta.attribute-with-value.class')
            is_id = score('meta.attribute-with-value.id')
            if not is_class and not is_id:
                return
        else:
            if not score('source'):
                return
            if score('comment'):
                return
            # Only show definitions in a string if there is interpolated source
            if score('string') and not score('string source'):
                return

        symbol, locations = symbol_at_point(view, point)
        locations = filter_current_symbol(view, point, symbol, locations)
        ref_locations = lookup_references(view.window(), symbol)
        ref_locations = filter_current_symbol(view, point, symbol, ref_locations)
        if not locations and not ref_locations:
            return

        # Don't add a jump point if the selection intersects the symbol at all
        save_point = point
        region = view.expand_by_class(
            point,
            sublime.CLASS_WORD_START | sublime.CLASS_WORD_END,
            "[]{}()<>:."
        )
        sel = view.sel()
        if len(sel) == 1 and (sel[0].a in region or sel[0].b in region):
            save_point = -1

        symbol_name = '&nbsp;{}&nbsp;<code>{}</code>'.format(
            'of' if locations else 'to', html.escape(symbol))

        sheet = view.sheet()
        group = sheet.group()
        if group is not None:
            selected_sheets = view.window().selected_sheets_in_group(group)
        else:
            selected_sheets = []

        relative_to_focused = view.settings().get("open_popup_definitions_relative_to_focused_view")
        open_tab = "Open Tab to Right" + (" of View" if not relative_to_focused else " of Focused View")

        primary = 'Cmd' if sys.platform == 'darwin' else 'Ctrl'
        title = primary + "+Click to " + open_tab
        if len(selected_sheets) > 1:
            if sheet != selected_sheets[-1]:
                title += "\nShift+Click to Append Tab to Current Selection"
            title += "\nAlt+Click to Replace All Tabs in Current Selection"

        link_markup = ('<span class="{class_name}" title="{name}">{letter}</span>'
                       '<a href="{href}" title="{title}">{location}</a>&nbsp;'
                       '<a class="icon" href="{new_tab_href}" '
                       'title="Open Tab to Right of Current Selection">◨</a>&nbsp;'
                       '<span class="syntax">{syntax}</span>')

        links = '<br>'.join(
            link_markup.format(
                class_name=_kind_class_name(l.kind[0]),
                letter=l.kind[1] if l.kind[1] else '&nbsp;',
                name=l.kind[2] if l.kind[2] else '',
                syntax=html.escape(l.syntax),
                location=format_location(l),
                href=_sym_def_href(l, add_jump_point=save_point, focus_view=view.id()),
                new_tab_href=_sym_def_href(l, new_tab=True, add_jump_point=save_point, focus_view=view.id()),
                title=title)
            for l in locations)

        if len(locations) > 0:
            plural = 's' if len(locations) > 1 else ''

            def_section = """
                <h1>Definition%s%s</h1>
                <p>%s</p>
            """ % (plural, symbol_name, links)

            symbol_name = ''
        else:
            def_section = ""

        ref_link_markup = ('<a href=\'{href}\' title="{title}">{location}</a>'
                           '&nbsp;<a class="icon" href=\'{new_tab_href}\' title="Open Tab to Right">◨</a>'
                           '&nbsp;<span class="syntax">{syntax}</span>')

        ref_links = '<br>'.join(
            ref_link_markup.format(
                syntax=html.escape(l.syntax),
                location=format_location(l),
                href=_sym_def_href(l, add_jump_point=save_point, focus_view=view.id()),
                new_tab_href=_sym_def_href(l, new_tab=True, add_jump_point=save_point, focus_view=view.id()),
                title=title)
            for l in ref_locations)

        if len(ref_locations) > 0:
            plural = 's' if len(ref_links) != 1 else ''

            ref_section = """
                <h1>Reference%s%s</h1>
                <p>%s</p>
            """ % (plural, symbol_name, ref_links)
            if len(def_section) != 0:
                ref_section = "<br>" + ref_section
        else:
            ref_section = ""

        body = """
            <body id=show-definitions>
                <style>
                    body {
                        font-family: system;
                    }
                    %s
                </style>
                %s
                %s
            </body>
        """ % (_popup_css(), def_section, ref_section)

        view.show_popup(
            body,
            flags=sublime.HIDE_ON_MOUSE_MOVE_AWAY,
            location=point,
            max_width=1024)
