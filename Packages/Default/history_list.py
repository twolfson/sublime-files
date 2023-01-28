"""
HistoryList
Remembers the history of navigation and provides ability to
jump backwards and forwards
"""

import sublime
import sublime_plugin

import sys
import time


if sys.version_info[:2] == (3, 3):
    import traceback

    importer = "unknown"
    for entry in reversed(traceback.extract_stack()[:-1]):
        if entry[0].startswith("<frozen importlib"):
            continue
        importer = entry[0]
        break
    print("error: Default.history_list was imported on Python 3.3 by \"%s\"" % importer)


class JumpRecord:
    __slots__ = ['key', 'view', 'sheets']

    def __init__(self, key, view, selections, sheets):
        # The View.get_regions() key to retrieve the selections
        self.key = key
        # The sublime.View to focus
        self.view = view
        # A set of sublime.Sheet objects to be selected
        self.sheets = sheets

        view.add_regions(key, selections)

    def __repr__(self):
        return 'JumpRecord(%r, %r, %r, %r)' % (
            self.key,
            self.view,
            self.selections,
            self.sheets
        )

    def __del__(self):
        self.view.erase_regions(self.key)

    def update(self, view, selections, sheets):
        """
        Update the record with new details

        :param view:
            The new sublime.View for the record

        :param selections:
            A list of sublime.Region objects to set the selections to

        :param sheets:
            A set of sublime.Sheet objects for the selected sheets
        """

        view.add_regions(self.key, selections)
        if self.view != view:
            self.view.erase_regions(self.key)
            self.view = view
        self.sheets = sheets

    @property
    def selections(self):
        """
        The selections are not stored in this object since modifications to
        the view will cause the regions to be moved. By storing the regions in
        the text buffer, it will deal with shifting them around.

        :return:
            A list of sublime.Region objects representing the selections
        """

        return self.view.get_regions(self.key)


def _log(message):
    """
    Prints a log to the console, prefixed by the plugin name

    :param message:
        A str of the message to print
    """

    print("history_list: %s" % message)


class JumpHistory:
    """
    Stores the current jump history
    """

    LOG = False
    LIST_LIMIT = 120
    TIME_BETWEEN_RECORDING = 1
    TIME_AFTER_ACTIVATE = 0.1

    def __init__(self):
        # A stack of JumpRecord objects
        self.history_list = []

        # The string name of the command the user most recently executed
        self.current_command = ""
        # If self.current_command was different from the preceeding command
        self.different_command = False

        # A float unix timestamp of when self.history_list was last modified
        self.last_change_time = 0
        # If the last modification to self.history_list was from on_activated()
        self.last_was_activation = False

        # A negative integer index in self.history_list of where the user is
        # located. This allows them to jump forward and backward.
        self.current_item = -1

        # Used to generate the region names where the selection is stored
        self.key_counter = 0

    def push_selection(self, view, selection=None, is_activation=False):
        """
        Possibly records the current selections in the view to the history.
        Will skip recording if the current state of the view would result in
        history entries the user would find confusing.

        :param view:
            A sublime.View object

        :param selection:
            None to use the view's current selection, otherwise a list of
            sublime.Region objects to use as the selections to record

        :param is_activation:
            A bool - if the push event is triggered by on_activated()
        """

        if (self.current_command == "jump_back" or
                self.current_command == "jump_forward" or
                self.current_command == "soft_undo" or
                self.current_command == "soft_redo" or
                self.current_command == "undo" or
                self.current_command == "redo_or_repeat" or
                self.current_command == "redo"):
            self.current_command = ":empty"
            return

        # We need the view to be loaded in order to interact with regions
        # and the selection
        if view.is_loading():
            kwargs = {
                "selection": selection,
                "is_activation": is_activation
            }
            sublime.set_timeout(
                lambda: self.push_selection(view, **kwargs), 100)
            return

        if selection is not None:
            cur_sel = selection

        else:
            cur_sel = list(view.sel())
            to_ignore = view.get_regions('jump_ignore_selection')
            if to_ignore:
                view.erase_regions('jump_ignore_selection')
            if to_ignore == cur_sel:
                if self.LOG:
                    _log("ignoring selection %r" % cur_sel)
                return

        sheets = set()
        window = view.window()
        if window:
            sheets = set(window.selected_sheets())

        temp_item = self.current_item
        if self.history_list != []:

            while True:
                record = self.history_list[temp_item]
                prev_sel = record.selections
                if prev_sel or temp_item <= -len(self.history_list):
                    break
                temp_item -= 1

            # Don't record duplicate history records
            if prev_sel and record.view == view and prev_sel == cur_sel:
                return

            # There are two situations in which we overwrite the previous
            # record:
            #  1. When a command is repeated in quick succession. This
            #     prevents lots of records when editing.
            #  2. When the last item was from on_activate, we don't want to
            #     mark that as a real record, otherwise things like
            #     Goto Definition result in two records the user has to jump
            #     back through.
            change = time.time() - self.last_change_time

            just_activated = change <= self.TIME_AFTER_ACTIVATE \
                and self.last_was_activation
            duplicate_command = change <= self.TIME_BETWEEN_RECORDING \
                and not self.different_command and record.view == view

            if just_activated or duplicate_command:
                record.update(view, cur_sel, sheets)
                if self.LOG:
                    _log("updated record %d to %r" % (temp_item, record))
                self.last_change_time = time.time()
                self.last_was_activation = False if just_activated \
                    else is_activation
                return

        if self.current_item != -1:
            delete_index = self.current_item + 1
            del self.history_list[delete_index:]
            self.current_item = -1
            if self.LOG:
                _log("removed newest %d records, pointer = -1" % abs(delete_index))

        key = self.generate_key()
        self.history_list.append(JumpRecord(key, view, cur_sel, sheets))
        if self.LOG:
            _log("adding %r" % self.history_list[-1])

        if len(self.history_list) > self.LIST_LIMIT:
            # We remove more than one at a time so we don't call this every time
            old_len = len(self.history_list)
            new_len = old_len - int(self.LIST_LIMIT / 3)
            if self.LOG:
                _log("removed oldest %d records, pointer = %d" % (old_len - new_len, self.current_item))
            del self.history_list[:new_len]

        self.last_change_time = time.time()
        self.last_was_activation = is_activation

        # This ensures the start of a drag_select gets a unique entry, but
        # then all subsequent selections get merged into a single entry
        if self.current_command == "post:drag_select":
            self.different_command = False
        elif self.current_command == 'drag_select':
            self.current_command = "post:drag_select"
            self.different_command = True

    def jump_back(self, in_widget):
        """
        Returns info about where the user should jump back to, modifying the
        index of the current item.

        :param in_widget:
            A bool indicating if the focus is currently on a widget. In this
            case we don't move the current_item, just jump to it.

        :return:
            A 3-element tuple:
            0: sublime.View - the view to focus on
            1: a list of sublime.Region objects to use as the selection
            2: a set of sublime.Sheet objects that should be selected
        """

        temp_item = self.current_item

        cur_record = self.history_list[temp_item]
        cur_sel = cur_record.selections

        while True:
            if temp_item == -len(self.history_list):
                return None, [], []

            if not in_widget:
                temp_item -= 1
            record = self.history_list[temp_item]
            record_sel = record.selections
            if in_widget:
                break

            if record_sel and (cur_record.view != record.view or
                               cur_sel != record_sel):
                if not cur_sel:
                    cur_sel = record_sel
                else:
                    break

        self.current_item = temp_item
        if self.LOG:
            _log("setting pointer = %d" % self.current_item)

        return record.view, record_sel, record.sheets

    def jump_forward(self, in_widget):
        """
        Returns info about where the user should jump forward to, modifying
        the index of the current item.

        :param in_widget:
            A bool indicating if the focus is currently on a widget. In this
            case we don't move the current_item, just jump to it.

        :return:
            A 3-element tuple:
            0: sublime.View - the view to focus on
            1: a list of sublime.Region objects to use as the selection
            2: a set of sublime.Sheet objects that should be selected
        """

        temp_item = self.current_item

        cur_record = self.history_list[temp_item]
        cur_sel = cur_record.selections

        while True:
            if temp_item == -1:
                return None, [], []

            if not in_widget:
                temp_item += 1
            record = self.history_list[temp_item]
            record_sel = record.selections
            if in_widget:
                break

            if record_sel and (cur_record.view != record.view or
                               cur_sel != record_sel):
                if not cur_sel:
                    cur_sel = record_sel
                else:
                    break

        self.current_item = temp_item
        if self.LOG:
            _log("setting pointer = %d" % self.current_item)

        return record.view, record_sel, record.sheets

    def set_current_item(self, index):
        """
        Modifies the index of the current item in the history list

        :param index:
            A negative integer, with -1 being the last item
        """

        self.current_item = index
        if self.LOG:
            _log("setting pointer = %d" % self.current_item)

    def record_command(self, command):
        """
        Records a command being run, used to determine when changes to the
        selection should be recorded

        :param command:
            A string of the command that was run. The string ":text_modified"
            should be passed when the buffer is modified. This is used in
            combination with the last command to ignore recording undo/redo
            changes.
        """

        self.different_command = self.current_command != command

        # We don't track text modifications when they occur due to
        # the undo/redo stack. Otherwise we'd end up pusing new
        # selections, and undo/redo is handled by
        # JumpHistoryUpdater.on_post_text_command().
        if (command == ":text_modified" and
                (self.current_command == "soft_undo" or
                 self.current_command == "soft_redo" or
                 self.current_command == "undo" or
                 self.current_command == "redo_or_repeat" or
                 self.current_command == "redo")):
            return

        self.current_command = command

    def reorient_current_item(self, view):
        """
        Find the index of the item in the history list that matches the
        current view state, and update the current_item with that

        :param view:
            The sublime.View object to use when finding the correct current
            item in the history list
        """

        cur_sel = list(view.sel())
        for i in range(-1, -len(self.history_list) - 1, -1):

            while True:
                record = self.history_list[i]
                record_sel = record.selections
                if record_sel or i <= -len(self.history_list):
                    break
                i -= 1

            if record_sel and record.view == view and record_sel == cur_sel:
                self.current_item = i
                if self.LOG:
                    _log("set pointer = %d" % self.current_item)
                return

    def remove_view(self, view):
        """
        Purges all history list items referring to a specific view

        :param view:
            The sublime.View being removed
        """

        sheet = view.sheet()
        removed = 0
        for i in range(-len(self.history_list), 0):
            record = self.history_list[i]
            if record.view == view:
                del self.history_list[i]
                removed += 1
                if self.current_item < i:
                    self.current_item += 1
            elif sheet in record.sheets:
                record.sheets.remove(sheet)
        if self.LOG:
            _log("removed %r including %d records, pointer = %d" % (view, removed, self.current_item))

    def generate_key(self):
        """
        Creates a key to be used with sublime.View.add_regions()

        :return:
            A string key to use when storing and retrieving regions
        """

        # generate enough keys for 5 times the jump history limit
        # this can still cause clashes as new history can be erased when we jump
        # back several steps and jump again.
        self.key_counter += 1
        self.key_counter %= self.LIST_LIMIT * 5
        return 'jump_key_' + hex(self.key_counter)


# dict from window id to JumpHistory
jump_history_dict = {}


def _history_for_window(window):
    """
    Fetches the JumpHistory object for the window

    :param window:
        A sublime.Window object

    :return:
        A JumpHistory object
    """

    global jump_history_dict

    if not window:
        return JumpHistory()
    else:
        return jump_history_dict.setdefault(window.id(), JumpHistory())


def _history_for_view(view):
    """
    Fetches the JumpHistory object for the window containing the view

    :param view:
        A sublime.View object

    :return:
        A JumpHistory object
    """

    return _history_for_window(view.window())


# Compatibility shim to not raise ImportError with Anaconda and other plugins
# that manipulated the JumpHistory in ST3
get_jump_history_for_view = _history_for_view


class JumpHistoryUpdater(sublime_plugin.EventListener):
    """
    Listens on the sublime text events and push the navigation history into the
    JumpHistory object
    """

    def _valid_view(self, view):
        """
        Determines if we want to track the history for a view

        :param view:
            A sublime.View object

        :return:
            A bool if we should track the view
        """

        return view is not None and not view.settings().get('is_widget')

    def on_modified(self, view):
        if not self._valid_view(view):
            return

        history = _history_for_view(view)
        if history.LOG:
            _log("%r was modified" % view)
        history.record_command(":text_modified")

    def on_selection_modified(self, view):
        if not self._valid_view(view):
            return

        history = _history_for_view(view)
        if history.LOG:
            _log("%r selection was changed" % view)
        history.push_selection(view)

    def on_activated(self, view):
        if not self._valid_view(view):
            return

        history = _history_for_view(view)
        if history.LOG:
            _log("%r was activated" % view)
        history.push_selection(view, is_activation=True)

    def on_text_command(self, view, name, args):
        if not self._valid_view(view):
            return

        history = _history_for_view(view)
        if history.LOG:
            _log("%r is about to run text command %r" % (view, name))
        history.record_command(name)

    def on_post_text_command(self, view, name, args):
        if not self._valid_view(view):
            return

        if name == "undo" or name == "redo_or_repeat" or name == "redo":
            _history_for_view(view).reorient_current_item(view)

        if name == "soft_redo":
            _history_for_view(view).set_current_item(-1)

    def on_window_command(self, window, name, args):
        view = window.active_view()
        if not self._valid_view(view):
            return

        history = _history_for_view(view)
        if history.LOG:
            _log("%r is about to run window command %r" % (view, name))
        history.record_command(name)

    # TODO: We need an on_pre_closed_sheet in the future since we currently
    # leave stale ImageSheet() and HtmlSheet() references in the JumpHistory.
    def on_pre_close(self, view):
        if not self._valid_view(view):
            return

        _history_for_view(view).remove_view(view)


class _JumpCommand(sublime_plugin.TextCommand):

    VALID_WIDGETS = {
        "find:input",
        "incremental_find:input",
        "replace:input:find",
        "replace:input:replace",
        "find_in_files:input:find",
        "find_in_files:input:location",
        "find_in_files:input:replace",
        "find_in_files:output",
    }

    def _get_window(self):
        """
        Returns the (non-widget) view to get the history for

        :return:
            None or a sublime.Window to get the history from
        """

        if not self.view.settings().get('is_widget') or \
                self.view.element() in self.VALID_WIDGETS:
            return self.view.window()

        return None

    def _perform_jump(self, window, view, selections, sheets):
        """
        Restores the window to the state where the view has the selections

        :param window:
            The sublime.Window containing the view

        :param view:
            The sublime.View to focus

        :param selections:
            A list of sublime.Region objects to set the selection to

        :param sheets:
            A list of sublime.Sheet objects that should be (minimally)
            selected. If the currently selected sheets is a superset of these,
            then no sheet selection changes will be made.
        """

        # Reduce churn by only selecting sheets when one is not visible
        if set(sheets) - set(window.selected_sheets()):
            window.select_sheets(sheets)
        window.focus_view(view)

        view.sel().clear()
        view.sel().add_all(selections)
        view.show(selections[0], True)

        sublime.status_message("")

    def is_enabled(self):
        return self._get_window() is not None


class JumpBackCommand(_JumpCommand):
    def run(self, edit):
        window = self._get_window()
        jump_history = _history_for_window(window)

        is_widget = self.view.settings().get('is_widget')
        view, selections, sheets = jump_history.jump_back(is_widget)
        if not selections:
            sublime.status_message("Already at the earliest position")
            return

        if jump_history.LOG:
            _log("jumping back to %r, %r, %r" % (view, selections, sheets))
        self._perform_jump(window, view, selections, sheets)


class JumpForwardCommand(_JumpCommand):
    def run(self, edit):
        window = self._get_window()
        jump_history = _history_for_window(window)

        is_widget = self.view.settings().get('is_widget')
        view, selections, sheets = jump_history.jump_forward(is_widget)
        if not selections:
            sublime.status_message("Already at the newest position")
            return

        if jump_history.LOG:
            _log("jumping forward to %r, %r, %r" % (view, selections, sheets))
        self._perform_jump(window, view, selections, sheets)


def _2_int_list(value):
    """
    :param value:
        The value to check

    :return:
        A bool is the value is a list with 2 ints
    """

    if not isinstance(value, list):
        return False

    if len(value) != 2:
        return False

    if not isinstance(value[0], int):
        return False

    return isinstance(value[1], int)


class AddJumpRecordCommand(sublime_plugin.TextCommand):
    """
    Allows packages to add a jump point without changing the selection
    """

    def run(self, edit, selection):
        if not self.view.settings().get('is_widget'):
            view = self.view
        else:
            view = self.view.window().active_view()

        regions = []
        type_error = False

        if isinstance(selection, int):
            regions.append(sublime.Region(selection, selection))

        elif isinstance(selection, list):
            if _2_int_list(selection):
                regions.append(sublime.Region(selection[0], selection[1]))
            else:
                for s in selection:
                    if _2_int_list(s):
                        regions.append(sublime.Region(s[0], s[1]))
                    elif isinstance(s, int):
                        regions.append(sublime.Region(s, s))
                    else:
                        type_error = True
                        break
        else:
            type_error = True

        if type_error:
            raise TypeError('selection must be an int, 2-int list, '
                            'or list of 2-int lists')

        jump_history = _history_for_window(view.window())
        jump_history.push_selection(view, selection=regions)


def plugin_unloaded():
    # Clean up the View region side-effects of the JumpRecord objects
    jump_history_dict.clear()
