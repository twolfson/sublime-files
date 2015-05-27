"""
HistoryList
Remembers the history of navigation and provides ability to
jump backwards and forwards
"""

import sublime, sublime_plugin

class JumpHistory():
    """
    Stores the current jump history
    """

    LIST_LIMIT = 120
    LIST_TRIMMED_SIZE = 100

    def __init__(self):
        self.history_list = []

        # current_item point to newest item of the queue, which is at the back of the
        # list. To make appending easier current_item is a negative index
        # current_item would be -1 to point to the newest item and -len to point to oldest
        self.current_item = 0
        self.key_counter = 0

    def push_selection(self, view):
        """
        Push the current selection of the view into this history.
        If we push a selection into history while current item is not pointing
        to head, anything before the current item is erased
        """
        region_list = list(view.sel())

        if region_list == []:
            return

        # we have just performed a jump back and then move again
        # delete every item after the current item
        self.clear_history_after_current()

        # check the newest entry is not the same as selection
        if self.history_list != []:
            first_view, first_key = self.history_list[-1]
            if first_view.view_id == view.view_id:
                first_sel = view.get_regions(first_key)
                if first_sel == region_list:
                    return

        key = self.generate_key()
        view.add_regions(key, region_list)

        # set the new selection as the current item, as a tuple (view_id, key)
        self.history_list.append((view, key))
        self.trim_selections()

    def jump_back(self, active_view):
        """
        Return the view and selection list to jump back to
        Jump back in history. If the current_item is -1, it also pushes the
        active view sel() into the history.
        """
        if self.current_item == 0:
            # we got no head, add one so we can jump back there
            # note that the push might not add anything if the region
            # is empty or if the region is the same as the previous
            # one, but we still increment current item. This is such
            # that the newest item is always the newest location
            self.push_selection(active_view)
            self.current_item = -1

        if self.current_item == -len(self.history_list):
            # already pointing to the oldest
            return None, []

        # get the next (older) selection
        self.current_item -= 1
        view, key = self.history_list[self.current_item]
        return view, view.get_regions(key)

    def jump_forward(self, active_view):
        if self.history_list == []:
            return None, []
        #already pointing to the front
        if self.current_item >= -1:
            return None, []
        # get the top selection
        # print(self.current_item)
        self.current_item += 1
        view, key = self.history_list[self.current_item]
        return view, view.get_regions(key)

    def remove_view(self, view_id):
        i = 0
        # use negative indices since current_item is negative
        # remove any selection that has the same view id
        # adjust the current_item, iterate from the back
        while (i > -len(self.history_list)):
            i -= 1
            if self.history_list[i][0].view_id == view_id:
                del self.history_list[i]
                if self.current_item <= i:
                    self.current_item += 1

    def generate_key(self):
        # generate enough keys for 5 times the jump history limit
        # this can still cause clashes as new history can be erased when we jump
        # back several steps and jump again.
        self.key_counter += 1
        self.key_counter %= self.LIST_LIMIT * 5
        return 'jump_key_' + hex(self.key_counter)

    def clear_history_after_current(self):
        if self.current_item == 0:
            return

        # remove all history that are newer than current
        for i in range(-1, self.current_item):
            view, key = self.history_list[i]
            view.erase_regions(key)
        del self.history_list[self.current_item + 1:]
        # set current_item to the imaginary back (current caret position not yet pushed)
        self.current_item = 0

    def trim_selections(self):
        if len(self.history_list) > self.LIST_LIMIT:
            # max reached, remove everything too old
            # trim to a smaller size to avoid doing on this every insert
            for i in range(0, len(self.history_list) - self.LIST_TRIMMED_SIZE):
                # erase the regions from view
                view, key = self.history_list[i]
                view.erase_regions(key)
            del self.history_list[: len(self.history_list) - self.LIST_TRIMMED_SIZE]

    def len(self):
        return len(self.history_list)

# dict from window id to JumpHistory
jump_history_dict = {}

def get_jump_history(window_id):
    global jump_history_dict
    return jump_history_dict.setdefault(window_id, JumpHistory())

def get_jump_history_for_view(view):
    win = view.window()
    if not win:
        return JumpHistory()
    else:
        return get_jump_history(win.id())

# remember that we are jumping and ignore
# on_deactivated callback
g_is_jumping = False

def lock_jump_history():
    global g_is_jumping
    g_is_jumping = True

def unlock_jump_history():
    global g_is_jumping
    g_is_jumping = False

class JumpHistoryUpdater(sublime_plugin.EventListener):
    """
    Listens on the sublime text events and push the navigation history into the
    JumpHistory object
    """
    def on_text_command(self, view, name, args):
        if view.settings().get('is_widget'):
            return
        # print(view.id())
        # print(name)
        if name == 'move' and args['by'] == 'pages':
            # syntax is {'by': 'lines', 'forward': True}
            get_jump_history_for_view(view).push_selection(view)
        elif name == 'drag_select':
            # using mouse to move cursor, we only want to capture
            # this if it is in the same view, otherwise on_deactivated()
            # will handle this
            if view.window().active_view() == view:
                get_jump_history_for_view(view).push_selection(view)
        elif name == 'move_to':
            where_to = args.get('to')
            if where_to == 'bof' or where_to == 'eof':
                # move to bof/eof
                get_jump_history_for_view(view).push_selection(view)

    def on_window_command(self, window, name, args):
        if name == 'goto_definition':
            view = window.active_view()
            if not view.settings().get('is_widget'):
                get_jump_history(window.id()).push_selection(view)

    def on_deactivated(self, view):
        if not g_is_jumping:
            if view.settings().get('is_widget'):
                return
            # check the property to ensure we don't add history
            # for a view that is dying
            if view.settings().get('history_list_is_closing'):
                return

            get_jump_history_for_view(view).push_selection(view)

    def on_pre_close(self, view):
        """ remove the history from the view """
        if view.settings().get('is_widget'):
            return
        # hack to add a property so that we know to ignore this
        # view on_deactivated
        view.settings().set('history_list_is_closing', True)
        get_jump_history_for_view(view).remove_view(view.id())
        unlock_jump_history()

class JumpBackCommand(sublime_plugin.TextCommand):
    """
    Defines a new text command "jump_back"
    """
    def run(self, edit):
        if self.view.settings().get('is_widget'):
            return

        # jump back in history
        # get the new selection
        jump_history = get_jump_history_for_view(self.view)

        view, region_list = jump_history.jump_back(self.view)
        if region_list == []:
            sublime.status_message("Already at the earliest position")
            return

        lock_jump_history()
        # inputs a dict where the first is the argument name
        #print(view.window(), region_list)
        # change to another view

        self.view.window().focus_view(view)
        view.sel().clear()
        view.sel().add_all(region_list)
        view.show(region_list[0], True)
        sublime.status_message("")
        unlock_jump_history()

class JumpForwardCommand(sublime_plugin.TextCommand):
    """
    Defines a new text command "jump_forward"
    """
    def run(self, edit):
        if self.view.settings().get('is_widget'):
            return

        # jump back in history
        # get the new selection
        jump_history = get_jump_history_for_view(self.view)
        view, region_list = jump_history.jump_forward(self.view)
        if region_list == []:
            sublime.status_message("Already at the newest position")
            return

        lock_jump_history()

        # inputs a dict where the first is the argument name
        # print(region_list)
        # change to another view
        self.view.window().focus_view(view)
        view.sel().clear()
        view.sel().add_all(region_list)
        # print(region_list)
        view.show(region_list[0], True)
        sublime.status_message("")

        unlock_jump_history()


# unit testing
# to run it in sublime text:
# import Default.history_list
# Default.history_list.Unittest.run()

import unittest

class Unittest(unittest.TestCase):

    class Sublime:
        pass

    class View:
        def __init__(self, id):
            self.view_id = id
            # just make it a list of regions
            self.region_list = [sublime.Region(0, 0)]
            self.key_to_region = {}

        def sel(self):
            return self.region_list

        def set_sel(self, region):
            self.region_list = [region]

        def add_regions(self, key, regions):
            self.key_to_region[key] = regions

        def get_regions(self, key):
            return self.key_to_region.get(key, [])

        def erase_regions(self, key):
            del self.key_to_region[key]

    def run():
        # redefine the modules to use the mock version
        global sublime

        sublime_module = sublime
        # use the normal region
        Unittest.Sublime.Region = sublime.Region
        sublime = Unittest.Sublime

        test = Unittest()
        test.test_simple_jump()
        test.test_duplicate_jump_history()
        test.test_jump_branch()

        # set it back after testing
        sublime = sublime_module

    def test_simple_jump(self):
        history = JumpHistory()
        view = Unittest.View(1)

        # create a new selection
        first_pos = sublime.Region(10, 10)
        view.set_sel(first_pos)

        # push
        history.push_selection(view)

        # go some where
        second_pos = sublime.Region(20, 10)
        view.set_sel(second_pos)

        # now try to jump back
        # should jump back to first pos
        self.assertEqual(history.jump_back(view)[1][0], first_pos)

        # now jump back again, should go no where
        self.assertEqual(history.jump_back(view)[1], [])

        # jump forward, should jump to where we were, this also test
        # that second_pos is automatically pushed when we jump back
        # from a new position
        self.assertEqual(history.jump_forward(view)[1][0], second_pos)

    # try to jump back two step and set new history
    def test_jump_branch(self):
        history = JumpHistory()
        view = Unittest.View(1)

        # create 3 jump positions
        pos_1 = sublime.Region(1, 1)
        view.set_sel(pos_1)
        history.push_selection(view)

        pos_2 = sublime.Region(2, 2)
        view.set_sel(pos_2)
        history.push_selection(view)

        pos_3 = sublime.Region(3, 3)
        view.set_sel(pos_3)
        history.push_selection(view)

        pos_4 = sublime.Region(4, 4)
        view.set_sel(pos_4)

        # now jump back to pos_2, and do few moves
        self.assertEqual(history.jump_back(view)[1][0], pos_3)
        self.assertEqual(history.jump_back(view)[1][0], pos_2)

        pos_3 = sublime.Region(3, 1)
        view.set_sel(pos_3)
        history.push_selection(view)

        pos_4 = sublime.Region(4, 1)
        view.set_sel(pos_4)
        history.push_selection(view)

        # now if I do a jump back i should get to pos_3
        self.assertEqual(history.jump_back(view)[1][0], pos_3)

        # back two more step should get to pos_1, show that history
        # before pos_2 is still there
        self.assertEqual(history.jump_back(view)[1][0], pos_2)
        self.assertEqual(history.jump_back(view)[1][0], pos_1)

        # test jumping forward again
        self.assertEqual(history.jump_forward(view)[1][0], pos_2)
        self.assertEqual(history.jump_forward(view)[1][0], pos_3)

    # test case where some jump history points are dups
    def test_duplicate_jump_history(self):
        history = JumpHistory()
        view = Unittest.View(1)

        # create a new selection
        first_pos = sublime.Region(10, 10)
        view.set_sel(first_pos)

        history.push_selection(view)
        history.push_selection(view)

        # go some where
        second_pos = sublime.Region(20, 10)
        view.set_sel(second_pos)
        history.push_selection(view)
        history.push_selection(view)

        # now jump back, should jump back to first pos
        # and ignore the previous two pushes
        self.assertEqual(history.jump_back(view)[1][0], first_pos)

        # now jump back again, should go no where
        self.assertEqual(history.jump_back(view)[1], [])

        # jump forward would still jump to second_pos
        self.assertEqual(history.jump_forward(view)[1][0], second_pos)

        # jump forward again would go no where
        self.assertEqual(history.jump_forward(view)[1], [])
