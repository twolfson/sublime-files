import sublime
import sublime_plugin


MAX_COLUMNS = 2


def create_splits(num_splits):
    return [0.0] + [1.0 / num_splits * i for i in range(1, num_splits)] + [1.0]


def rows_cols_for_panes(num_panes, max_columns):
    if num_panes > max_columns:
        num_cols = max_columns
        num_rows = num_panes - num_cols + 1
    else:
        num_cols = num_panes
        num_rows = 1
    return num_rows, num_cols


def assign_cells(num_panes, max_columns):
    num_rows, num_cols = rows_cols_for_panes(num_panes, max_columns)

    cells = []
    for i in range(0, num_panes):
        if i < (max_columns - 1):
            cells.append([i, 0, i + 1, num_rows])
        else:
            row = i - (max_columns - 1)
            cells.append([num_cols - 1, row, num_cols, row + 1])
    return cells


def move_sheets(window, src_group, dst_group):
    sheets = window.sheets_in_group(src_group)
    transient = window.transient_sheet_in_group(src_group)

    for i in range(len(sheets)):
        window.set_sheet_index(sheets[i], dst_group, i)

    if transient is not None:
        window.set_sheet_index(transient, dst_group, -1)


def num_sheets_in_group_including_transient(window, group):
    num = len(window.sheets_in_group(group))
    if window.transient_sheet_in_group(group) is not None:
        num += 1
    return num


class NewPaneCommand(sublime_plugin.WindowCommand):
    def new_pane(self, window, move_sheet, max_columns):
        cur_sheet = window.active_sheet()

        layout = window.get_layout()
        num_panes = len(layout["cells"])

        cur_index = window.active_group()

        rows = layout["rows"]
        cols = layout["cols"]
        cells = layout["cells"]

        if cells != assign_cells(num_panes, max_columns):
            # Current layout doesn't follow the automatic method, reset everyting
            num_rows, num_cols = rows_cols_for_panes(num_panes + 1, max_columns)
            rows = create_splits(num_rows)
            cols = create_splits(num_cols)
            cells = assign_cells(num_panes + 1, max_columns)
        else:
            # Adjust the current layout, keeping the user selected column widths
            # where possible
            num_cols = len(cols) - 1
            num_rows = len(rows) - 1

            # insert a new row or a new col
            if num_cols < max_columns:
                num_cols += 1
                cols = create_splits(num_cols)
            else:
                num_rows += 1
                rows = create_splits(num_rows)

            cells = assign_cells(num_panes + 1, max_columns)

        window.set_layout({'cells': cells, 'rows': rows, 'cols': cols})
        window.settings().set('last_automatic_layout', cells)

        # Move all the sheets so the new pane is created in the correct location
        for i in reversed(range(0, num_panes - cur_index - 1)):
            move_sheets(window, cur_index + i + 1, cur_index + i + 2)

        if move_sheet:
            transient = window.transient_sheet_in_group(cur_index)
            if transient is not None and cur_sheet.sheet_id == transient.sheet_id:
                # transient sheets may only be moved to index -1
                window.set_sheet_index(cur_sheet, cur_index + 1, -1)
            else:
                window.set_sheet_index(cur_sheet, cur_index + 1, 0)

            if num_sheets_in_group_including_transient(window, cur_index) == 0:
                window.focus_group(cur_index)
                window.new_file(sublime.TRANSIENT)

            window.focus_group(cur_index + 1)
        else:
            window.focus_group(cur_index + 1)
            window.new_file(sublime.TRANSIENT)

    def run(self, move=True):
        max_columns = self.window.template_settings().get('max_columns', MAX_COLUMNS)
        self.new_pane(self.window, move, max_columns)


class ClosePaneCommand(sublime_plugin.WindowCommand):
    def close_pane(self, window, idx, max_columns):
        layout = window.get_layout()
        num_panes = len(layout["cells"])
        selected_sheet = window.active_sheet_in_group(idx)

        if num_panes == 1:
            return

        for i in range(idx, window.num_groups()):
            move_sheets(window, i, i - 1)

        rows = layout["rows"]
        cols = layout["cols"]
        cells = layout["cells"]

        if layout["cells"] != assign_cells(num_panes, max_columns):
            num_rows, num_cols = rows_cols_for_panes(num_panes - 1, max_columns)
            rows = create_splits(num_rows)
            cols = create_splits(num_cols)
            cells = assign_cells(num_panes - 1, max_columns)
        else:
            num_cols = len(cols) - 1
            num_rows = len(rows) - 1

            if num_rows > 1:
                num_rows -= 1
                rows = create_splits(num_rows)
            else:
                num_cols -= 1
                cols = create_splits(num_cols)

            cells = assign_cells(num_panes - 1, max_columns)

        window.set_layout({'cells': cells, 'rows': rows, 'cols': cols})
        window.settings().set('last_automatic_layout', cells)

        new_idx = idx - 1
        if new_idx < 0:
            new_idx = 0
        window.focus_group(new_idx)
        window.focus_sheet(selected_sheet)

    def run(self, group=-1):
        if group < 0:
            group = self.window.active_group()
        max_columns = self.window.template_settings().get('max_columns', MAX_COLUMNS)
        self.close_pane(self.window, group, max_columns)


def is_automatic_layout(window):
    last_automatic_layout = window.settings().get('last_automatic_layout')
    if last_automatic_layout is None:
        return False

    if window.get_layout()['cells'] != last_automatic_layout:
        window.settings().erase('last_automatic_layout')
        return False

    return True


class AutomaticPaneCloser(sublime_plugin.EventListener):
    def on_activated(self, view):
        # Check for empty groups here, to handle tabs being dragged out of their
        # group
        sublime.set_timeout(lambda: self.on_close(view), 0)

    def on_close(self, view):
        window = sublime.active_window()

        if not is_automatic_layout(window):
            return

        # Maintain the focused group, which is required if the group being
        # closed is not focused (perhaps sheet was closed with the mouse)
        focused_group = window.active_group()

        for i in reversed(range(window.num_groups())):
            if num_sheets_in_group_including_transient(window, i) == 0:
                if i == focused_group:
                    focused_group = -1
                elif i < focused_group:
                    focused_group -= 1

                window.run_command('close_pane', {'group': i})
                if focused_group >= 0:
                    window.focus_group(focused_group)
                break


class FocusNeighboringGroup(sublime_plugin.WindowCommand):
    def run(self, forward=True):
        group = self.window.active_group()
        if forward:
            group = (group + 1) % self.window.num_groups()
        else:
            group = (group - 1) % self.window.num_groups()

        self.window.focus_group(group)


class MoveToNeighboringGroup(sublime_plugin.WindowCommand):
    def run(self, forward=True):
        group = self.window.active_group()
        if forward:
            group = (group + 1) % self.window.num_groups()
        else:
            group = (group - 1) % self.window.num_groups()

        self.window.run_command("move_to_group", {"group": group})


class SetMaxColumns(sublime_plugin.WindowCommand):
    def run(self, columns):
        if columns >= 1:
            max_columns = columns
            self.window.template_settings().set('max_columns', max_columns)

            # Update the layout
            layout = self.window.get_layout()
            num_panes = len(layout["cells"])

            num_rows, num_cols = rows_cols_for_panes(num_panes, max_columns)
            rows = create_splits(num_rows)
            cols = create_splits(num_cols)
            cells = assign_cells(num_panes, max_columns)
            self.window.set_layout({'cells': cells, 'rows': rows, 'cols': cols})
            self.window.settings().set('last_automatic_layout', cells)

    def is_checked(self, columns):
        if not is_automatic_layout(self.window):
            return False

        max_columns = self.window.template_settings().get('max_columns', MAX_COLUMNS)
        return columns == max_columns
