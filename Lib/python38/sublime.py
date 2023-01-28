"""
"""

# Don't evaluate type annotations at runtime
from __future__ import annotations

import collections
import html
import json
import sys
import io
import enum
from typing import Callable, Optional, Any, Iterator, Literal, TYPE_CHECKING

import sublime_api

if TYPE_CHECKING:
    from sublime_types import DIP, Vector, Point, Value, CommandArgs, Kind, Event, CompletionValue


class _LogWriter(io.TextIOBase):
    def __init__(self):
        self.buf = None

    def flush(self):
        b = self.buf
        self.buf = None
        if b is not None and len(b):
            sublime_api.log_message(b)

    def write(self, s):
        if self.buf is None:
            self.buf = s
        else:
            self.buf += s
        if '\n' in s or '\r' in s:
            self.flush()


sys.stdout = _LogWriter()  # type: ignore
sys.stderr = _LogWriter()  # type: ignore


class HoverZone(enum.IntEnum):
    """
    A zone in an open text sheet where the mouse may hover.

    See `EventListener.on_hover` and `ViewEventListener.on_hover`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``HOVER_`` prefix.

    .. since:: 4132 3.8
    """

    TEXT = 1
    """ The mouse is hovered over the text. """
    GUTTER = 2
    """ The mouse is hovered over the gutter. """
    MARGIN = 3
    """ The mouse is hovered in the white space to the right of a line. """


HOVER_TEXT = HoverZone.TEXT
HOVER_GUTTER = HoverZone.GUTTER
HOVER_MARGIN = HoverZone.MARGIN


class NewFileFlags(enum.IntFlag):
    """
    Flags for creating/opening files in various ways.

    See `Window.new_html_sheet`, `Window.new_file` and `Window.open_file`.

    For backwards compatibility these values are also available outside this
    enumeration (without a prefix).

    .. since:: 4132 3.8
    """

    NONE = 0
    """ """
    ENCODED_POSITION = 1
    """
    Indicates that the file name should be searched for a ``:row`` or
    ``:row:col`` suffix.
    """
    TRANSIENT = 4
    """
    Open the file as a preview only: it won't have a tab assigned it until
    modified.
    """
    FORCE_GROUP = 8
    """
    Don't select the file if it is open in a different group. Instead make a new
    clone of that file in the desired group.
    """
    SEMI_TRANSIENT = 16
    """
    If a sheet is newly created, it will be set to semi-transient.
    Semi-transient sheets generally replace other semi-transient sheets. This
    is used for the side-bar preview. Only valid with `ADD_TO_SELECTION` or
    `REPLACE_MRU`.

    .. since:: 4096
    """
    ADD_TO_SELECTION = 32
    """
    Add the file to the currently selected sheets in the group.

    .. since:: 4050
    """
    REPLACE_MRU = 64
    """
    Causes the sheet to replace the most-recently used sheet in the current sheet selection.

    .. since:: 4096
    """
    CLEAR_TO_RIGHT = 128
    """
    All currently selected sheets to the right of the most-recently used sheet
    will be unselected before opening the file. Only valid in combination with
    `ADD_TO_SELECTION`.

    .. since:: 4100
    """
    FORCE_CLONE = 256
    """
    Don't select the file if it is open. Instead make a new clone of that file in the desired
    group.

    .. :since:: next
    """


ENCODED_POSITION = NewFileFlags.ENCODED_POSITION
TRANSIENT = NewFileFlags.TRANSIENT
FORCE_GROUP = NewFileFlags.FORCE_GROUP
SEMI_TRANSIENT = NewFileFlags.SEMI_TRANSIENT
ADD_TO_SELECTION = NewFileFlags.ADD_TO_SELECTION
REPLACE_MRU = NewFileFlags.REPLACE_MRU
CLEAR_TO_RIGHT = NewFileFlags.CLEAR_TO_RIGHT
FORCE_CLONE = NewFileFlags.FORCE_CLONE


class FindFlags(enum.IntFlag):
    """
    Flags for use when searching through a `View`.

    See `View.find` and `View.find_all`.

    For backwards compatibility these values are also available outside this
    enumeration (without a prefix).

    .. since:: 4132 3.8
    """
    NONE = 0
    """ """
    IGNORECASE = 2
    """ Whether case should be considered when matching the find pattern. """
    LITERAL = 1
    """ Whether the find pattern should be matched literally or as a regex. """


IGNORECASE = FindFlags.IGNORECASE
LITERAL = FindFlags.LITERAL


class QuickPanelFlags(enum.IntFlag):
    """
    Flags for use with a quick panel.

    See `Window.show_quick_panel`.

    For backwards compatibility these values are also available outside this
    enumeration (without a prefix).

    .. since:: 4132 3.8
    """

    NONE = 0
    """ """
    MONOSPACE_FONT = 1
    """ Use a monospace font. """
    KEEP_OPEN_ON_FOCUS_LOST = 2
    """ Keep the quick panel open if the window loses input focus. """
    WANT_EVENT = 4
    """
    Pass a second parameter to the ``on_done`` callback, a `Event`.

    .. since:: 4096
    """


MONOSPACE_FONT = QuickPanelFlags.MONOSPACE_FONT
KEEP_OPEN_ON_FOCUS_LOST = QuickPanelFlags.KEEP_OPEN_ON_FOCUS_LOST
WANT_EVENT = QuickPanelFlags.WANT_EVENT


class PopupFlags(enum.IntFlag):
    """
    Flags for use with popups.

    See `View.show_popup`.

    For backwards compatibility these values are also available outside this
    enumeration (without a prefix).

    .. since:: 4132 3.8
    """
    NONE = 0
    """ """
    COOPERATE_WITH_AUTO_COMPLETE = 2
    """ Causes the popup to display next to the auto complete menu. """
    HIDE_ON_MOUSE_MOVE = 4
    """
    Causes the popup to hide when the mouse is moved, clicked or scrolled.
    """
    HIDE_ON_MOUSE_MOVE_AWAY = 8
    """
    Causes the popup to hide when the mouse is moved (unless towards the popup),
    or when clicked or scrolled.
    """
    KEEP_ON_SELECTION_MODIFIED = 16
    """
    Prevent the popup from hiding when the selection is modified.

    .. since:: 4057
    """
    HIDE_ON_CHARACTER_EVENT = 32
    """
    Hide the popup when a character is typed.

    .. since:: 4057
    """


# Deprecated
HTML = 1
COOPERATE_WITH_AUTO_COMPLETE = PopupFlags.COOPERATE_WITH_AUTO_COMPLETE
HIDE_ON_MOUSE_MOVE = PopupFlags.HIDE_ON_MOUSE_MOVE
HIDE_ON_MOUSE_MOVE_AWAY = PopupFlags.HIDE_ON_MOUSE_MOVE_AWAY
KEEP_ON_SELECTION_MODIFIED = PopupFlags.KEEP_ON_SELECTION_MODIFIED
HIDE_ON_CHARACTER_EVENT = PopupFlags.HIDE_ON_CHARACTER_EVENT


class RegionFlags(enum.IntFlag):
    """
    Flags for use with added regions. See `View.add_regions`.

    For backwards compatibility these values are also available outside this
    enumeration (without a prefix).

    .. since:: 4132 3.8
    """
    NONE = 0
    """ """
    DRAW_EMPTY = 1
    """ Draw empty regions with a vertical bar. By default, they aren't drawn at all. """
    HIDE_ON_MINIMAP = 2
    """ Don't show the regions on the minimap. """
    DRAW_EMPTY_AS_OVERWRITE = 4
    """ Draw empty regions with a horizontal bar instead of a vertical one. """
    PERSISTENT = 16
    """ Save the regions in the session. """
    DRAW_NO_FILL = 32
    """ Disable filling the regions, leaving only the outline. """
    HIDDEN = 128
    """ Don't draw the regions.  """
    DRAW_NO_OUTLINE = 256
    """ Disable drawing the outline of the regions. """
    DRAW_SOLID_UNDERLINE = 512
    """ Draw a solid underline below the regions. """
    DRAW_STIPPLED_UNDERLINE = 1024
    """ Draw a stippled underline below the regions. """
    DRAW_SQUIGGLY_UNDERLINE = 2048
    """ Draw a squiggly underline below the regions. """
    NO_UNDO = 8192
    """ """


DRAW_EMPTY = RegionFlags.DRAW_EMPTY
HIDE_ON_MINIMAP = RegionFlags.HIDE_ON_MINIMAP
DRAW_EMPTY_AS_OVERWRITE = RegionFlags.DRAW_EMPTY_AS_OVERWRITE
PERSISTENT = RegionFlags.PERSISTENT
DRAW_NO_FILL = RegionFlags.DRAW_NO_FILL
# Deprecated, use DRAW_NO_FILL instead
DRAW_OUTLINED = DRAW_NO_FILL
DRAW_NO_OUTLINE = RegionFlags.DRAW_NO_OUTLINE
DRAW_SOLID_UNDERLINE = RegionFlags.DRAW_SOLID_UNDERLINE
DRAW_STIPPLED_UNDERLINE = RegionFlags.DRAW_STIPPLED_UNDERLINE
DRAW_SQUIGGLY_UNDERLINE = RegionFlags.DRAW_SQUIGGLY_UNDERLINE
NO_UNDO = RegionFlags.NO_UNDO
HIDDEN = RegionFlags.HIDDEN


class QueryOperator(enum.IntEnum):
    """
    Enumeration of operators able to be used when querying contexts.

    See `EventListener.on_query_context` and
    `ViewEventListener.on_query_context`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``OP_`` prefix.

    .. since:: 4132 3.8
    """
    EQUAL = 0
    """ """
    NOT_EQUAL = 1
    """ """
    REGEX_MATCH = 2
    """ """
    NOT_REGEX_MATCH = 3
    """ """
    REGEX_CONTAINS = 4
    """ """
    NOT_REGEX_CONTAINS = 5
    """ """


OP_EQUAL = QueryOperator.EQUAL
OP_NOT_EQUAL = QueryOperator.NOT_EQUAL
OP_REGEX_MATCH = QueryOperator.REGEX_MATCH
OP_NOT_REGEX_MATCH = QueryOperator.NOT_REGEX_MATCH
OP_REGEX_CONTAINS = QueryOperator.REGEX_CONTAINS
OP_NOT_REGEX_CONTAINS = QueryOperator.NOT_REGEX_CONTAINS


class PointClassification(enum.IntFlag):
    """
    Flags that identify characteristics about a `Point` in a text sheet. See
    `View.classify`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``CLASS_`` prefix.

    .. since:: 4132 3.8
    """
    NONE = 0
    """ """
    WORD_START = 1
    """ The point is the start of a word. """
    WORD_END = 2
    """ The point is the end of a word. """
    PUNCTUATION_START = 4
    """ The point is the start of a sequence of punctuation characters. """
    PUNCTUATION_END = 8
    """ The point is the end of a sequence of punctuation characters. """
    SUB_WORD_START = 16
    """ The point is the start of a sub-word. """
    SUB_WORD_END = 32
    """ The point is the end of a sub-word. """
    LINE_START = 64
    """ The point is the start of a line. """
    LINE_END = 128
    """ The point is the end of a line. """
    EMPTY_LINE = 256
    """ The point is an empty line. """


CLASS_WORD_START = PointClassification.WORD_START
CLASS_WORD_END = PointClassification.WORD_END
CLASS_PUNCTUATION_START = PointClassification.PUNCTUATION_START
CLASS_PUNCTUATION_END = PointClassification.PUNCTUATION_END
CLASS_SUB_WORD_START = PointClassification.SUB_WORD_START
CLASS_SUB_WORD_END = PointClassification.SUB_WORD_END
CLASS_LINE_START = PointClassification.LINE_START
CLASS_LINE_END = PointClassification.LINE_END
CLASS_EMPTY_LINE = PointClassification.EMPTY_LINE


class AutoCompleteFlags(enum.IntFlag):
    """
    Flags controlling how asynchronous completions function. See
    `CompletionList`.

    For backwards compatibility these values are also available outside this
    enumeration (without a prefix).

    .. since:: 4132 3.8
    """
    NONE = 0
    """ """
    INHIBIT_WORD_COMPLETIONS = 8
    """
    Prevent Sublime Text from showing completions based on the contents of the
    view.
    """
    INHIBIT_EXPLICIT_COMPLETIONS = 16
    """
    Prevent Sublime Text from showing completions based on
    :path:`.sublime-completions` files.
    """
    DYNAMIC_COMPLETIONS = 32
    """
    If completions should be re-queried as the user types.

    .. since:: 4057
    """
    INHIBIT_REORDER = 128
    """
    Prevent Sublime Text from changing the completion order.

    .. since:: 4074
    """


INHIBIT_WORD_COMPLETIONS = AutoCompleteFlags.INHIBIT_WORD_COMPLETIONS
INHIBIT_EXPLICIT_COMPLETIONS = AutoCompleteFlags.INHIBIT_EXPLICIT_COMPLETIONS
DYNAMIC_COMPLETIONS = AutoCompleteFlags.DYNAMIC_COMPLETIONS
INHIBIT_REORDER = AutoCompleteFlags.INHIBIT_REORDER


class CompletionItemFlags(enum.IntFlag):
    """ :meta private: """
    NONE = 0
    KEEP_PREFIX = 1


COMPLETION_FLAG_KEEP_PREFIX = CompletionItemFlags.KEEP_PREFIX


class DialogResult(enum.IntEnum):
    """
    The result from a *yes / no / cancel* dialog. See `yes_no_cancel_dialog`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``DIALOG_`` prefix.

    .. since:: 4132 3.8
    """
    CANCEL = 0
    """ """
    YES = 1
    """ """
    NO = 2
    """ """


DIALOG_CANCEL = DialogResult.CANCEL
DIALOG_YES = DialogResult.YES
DIALOG_NO = DialogResult.NO


class UIElement(enum.IntEnum):
    """ :meta private: """
    SIDE_BAR = 1
    MINIMAP = 2
    TABS = 4
    STATUS_BAR = 8
    MENU = 16
    OPEN_FILES = 32


class PhantomLayout(enum.IntEnum):
    """
    How a `Phantom` should be positioned. See `PhantomSet`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``LAYOUT_`` prefix.

    .. since:: 4132 3.8
    """
    INLINE = 0
    """
    The phantom is positioned inline with the text at the beginning of its
    `Region`.
    """
    BELOW = 1
    """
    The phantom is positioned below the line, left-aligned with the beginning of
    its `Region`.
    """
    BLOCK = 2
    """
    The phantom is positioned below the line, left-aligned with the beginning of
    the line.
    """


LAYOUT_INLINE = PhantomLayout.INLINE
LAYOUT_BELOW = PhantomLayout.BELOW
LAYOUT_BLOCK = PhantomLayout.BLOCK


class KindId(enum.IntEnum):
    """
    For backwards compatibility these values are also available outside this
    enumeration with a ``KIND_ID_`` prefix.

    .. since:: 4132 3.8
    """
    AMBIGUOUS = 0
    """ """
    KEYWORD = 1
    """ """
    TYPE = 2
    """ """
    FUNCTION = 3
    """ """
    NAMESPACE = 4
    """ """
    NAVIGATION = 5
    """ """
    MARKUP = 6
    """ """
    VARIABLE = 7
    """ """
    SNIPPET = 8
    """ """

    # These should only be used for QuickPanelItem
    # and ListInputItem, not for CompletionItem
    COLOR_REDISH = 9
    """ """
    COLOR_ORANGISH = 10
    """ """
    COLOR_YELLOWISH = 11
    """ """
    COLOR_GREENISH = 12
    """ """
    COLOR_CYANISH = 13
    """ """
    COLOR_BLUISH = 14
    """ """
    COLOR_PURPLISH = 15
    """ """
    COLOR_PINKISH = 16
    """ """
    COLOR_DARK = 17
    """ """
    COLOR_LIGHT = 18
    """ """


KIND_ID_AMBIGUOUS = KindId.AMBIGUOUS
KIND_ID_KEYWORD = KindId.KEYWORD
KIND_ID_TYPE = KindId.TYPE
KIND_ID_FUNCTION = KindId.FUNCTION
KIND_ID_NAMESPACE = KindId.NAMESPACE
KIND_ID_NAVIGATION = KindId.NAVIGATION
KIND_ID_MARKUP = KindId.MARKUP
KIND_ID_VARIABLE = KindId.VARIABLE
KIND_ID_SNIPPET = KindId.SNIPPET
KIND_ID_COLOR_REDISH = KindId.COLOR_REDISH
KIND_ID_COLOR_ORANGISH = KindId.COLOR_ORANGISH
KIND_ID_COLOR_YELLOWISH = KindId.COLOR_YELLOWISH
KIND_ID_COLOR_GREENISH = KindId.COLOR_GREENISH
KIND_ID_COLOR_CYANISH = KindId.COLOR_CYANISH
KIND_ID_COLOR_BLUISH = KindId.COLOR_BLUISH
KIND_ID_COLOR_PURPLISH = KindId.COLOR_PURPLISH
KIND_ID_COLOR_PINKISH = KindId.COLOR_PINKISH
KIND_ID_COLOR_DARK = KindId.COLOR_DARK
KIND_ID_COLOR_LIGHT = KindId.COLOR_LIGHT

KIND_AMBIGUOUS = (KindId.AMBIGUOUS, "", "")
"""
.. since:: 4052
"""
KIND_KEYWORD = (KindId.KEYWORD, "", "")
"""
.. since:: 4052
"""
KIND_TYPE = (KindId.TYPE, "", "")
"""
.. since:: 4052
"""
KIND_FUNCTION = (KindId.FUNCTION, "", "")
"""
.. since:: 4052
"""
KIND_NAMESPACE = (KindId.NAMESPACE, "", "")
"""
.. since:: 4052
"""
KIND_NAVIGATION = (KindId.NAVIGATION, "", "")
"""
.. since:: 4052
"""
KIND_MARKUP = (KindId.MARKUP, "", "")
"""
.. since:: 4052
"""
KIND_VARIABLE = (KindId.VARIABLE, "", "")
"""
.. since:: 4052
"""
KIND_SNIPPET = (KindId.SNIPPET, "s", "Snippet")
"""
.. since:: 4052
"""


class SymbolSource(enum.IntEnum):
    """
    See `Window.symbol_locations`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``SYMBOL_SOURCE_`` prefix.

    .. since:: 4132 3.8
    """
    ANY = 0
    """
    Use any source - both the index and open files.

    .. since:: 4085
    """
    INDEX = 1
    """
    Use the index created when scanning through files in a project folder.

    .. since:: 4085
    """
    OPEN_FILES = 2
    """
    Use the open files, unsaved or otherwise.

    .. since:: 4085
    """


SYMBOL_SOURCE_ANY = SymbolSource.ANY
SYMBOL_SOURCE_INDEX = SymbolSource.INDEX
SYMBOL_SOURCE_OPEN_FILES = SymbolSource.OPEN_FILES


class SymbolType(enum.IntEnum):
    """
    See `Window.symbol_locations` and `View.indexed_symbol_regions`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``SYMBOL_TYPE_`` prefix.

    .. since:: 4132 3.8
    """
    ANY = 0
    """ Any symbol type - both definitions and references.

    .. since:: 4085
    """
    DEFINITION = 1
    """
    Only definitions.

    .. since:: 4085
    """
    REFERENCE = 2
    """
    Only references.

    .. since:: 4085
    """


SYMBOL_TYPE_ANY = SymbolType.ANY
SYMBOL_TYPE_DEFINITION = SymbolType.DEFINITION
SYMBOL_TYPE_REFERENCE = SymbolType.REFERENCE


class CompletionFormat(enum.IntEnum):
    """
    The format completion text can be in. See `CompletionItem`.

    For backwards compatibility these values are also available outside this
    enumeration with a ``COMPLETION_FORMAT_`` prefix.

    .. since:: 4132 3.8
    """

    TEXT = 0
    """
    Plain text, upon completing the text is inserted verbatim.

    .. since:: 4050
    """
    SNIPPET = 1
    """
    A snippet, with ``$`` variables. See also
    `CompletionItem.snippet_completion`.

    .. since:: 4050
    """
    COMMAND = 2
    """
    A command string, in the format returned by `format_command()`. See also
    `CompletionItem.command_completion()`.

    .. since:: 4050
    """


COMPLETION_FORMAT_TEXT = CompletionFormat.TEXT
COMPLETION_FORMAT_SNIPPET = CompletionFormat.SNIPPET
COMPLETION_FORMAT_COMMAND = CompletionFormat.COMMAND


def version() -> str:
    """
    :returns: The version number.
    """
    return sublime_api.version()


def platform() -> Literal["osx", "linux", "windows"]:
    """
    :returns: The platform which the plugin is being run on.
    """
    return sublime_api.platform()


def arch() -> Literal["x32", "x64", "arm64"]:
    """
    :returns: The CPU architecture.
    """
    return sublime_api.architecture()


def channel() -> Literal["dev", "stable"]:
    """
    :returns: The release channel of this build of Sublime Text.
    """
    return sublime_api.channel()


def executable_path() -> str:
    """
    .. since:: 4081
        This may be called at import time.

    :returns: The path to the main Sublime Text executable.
    """
    return sublime_api.executable_path()


def executable_hash() -> tuple[str, str, str]:
    """
    .. since:: 4081
        This may be called at import time.

    :returns: A tuple uniquely identifying the installation of Sublime Text.
    """
    import hashlib
    return (
        version(), platform() + '_' + arch(),
        hashlib.md5(open(executable_path(), 'rb').read()).hexdigest())


def packages_path() -> str:
    """
    .. since:: 4081
        This may be called at import time.

    :returns: The path to the "Packages" folder.
    """
    return sublime_api.packages_path()


def installed_packages_path() -> str:
    """
    .. since:: 4081
        This may be called at import time.

    :returns: The path to the "Installed Packages" folder.
    """
    return sublime_api.installed_packages_path()


def cache_path() -> str:
    """
    .. since:: 4081
        This may be called at import time.

    :returns: The path where Sublime Text stores cache files.
    """
    return sublime_api.cache_path()


def status_message(msg: str):
    """ Show a message in the status bar. """
    sublime_api.status_message(msg)


def error_message(msg: str):
    """ Display an error dialog. """
    sublime_api.error_message(msg)


def message_dialog(msg: str):
    """ Display a message dialog. """
    sublime_api.message_dialog(msg)


def ok_cancel_dialog(msg: str, ok_title="", title="") -> bool:
    """
    Show a *ok / cancel* question dialog.

    :param msg: The message to show in the dialog.
    :param ok_title: Text to display on the *ok* button.
    :param title: Title for the dialog. Windows only. :since:`4099`

    :returns: Whether the user pressed the *ok* button.
    """
    return sublime_api.ok_cancel_dialog(msg, title, ok_title)


def yes_no_cancel_dialog(msg: str, yes_title="", no_title="", title="") -> DialogResult:
    """
    Show a *yes / no / cancel* question dialog.

    :param msg: The message to show in the dialog.
    :param yes_title: Text to display on the *yes* button.
    :param no_title: Text to display on the *no* button.
    :param title: Title for the dialog. Windows only. :since:`4099`
    """
    return DialogResult(sublime_api.yes_no_cancel_dialog(msg, title, yes_title, no_title))


def open_dialog(
        callback: Callable[[str | list[str] | None], None],
        file_types: list[tuple[str, list[str]]] = [],
        directory: Optional[str] = None,
        multi_select=False,
        allow_folders=False):
    """
    Show the open file dialog.

    .. since:: 4075

    :param callback: Called with selected path(s) or ``None`` once the dialog is closed.
    :param file_types: A list of allowed file types, consisting of a description
                       and a list of allowed extensions.
    :param directory: The directory the dialog should start in.  Will use the
                      virtual working directory if not provided.
    :param multi_select: Whether to allow selecting multiple files. When ``True``
                         the callback will be called with a list.
    :param allow_folders: Whether to also allow selecting folders. Only works on
                          macOS. If you only want to select folders use
                          `select_folder_dialog`.
    """
    flags = 0
    if multi_select:
        flags |= 1
    if allow_folders:
        flags |= 2

    cb = callback
    if not multi_select:
        cb = lambda files: callback(files[0] if files else None)

    sublime_api.open_dialog(file_types, directory or '', flags, cb)


def save_dialog(
        callback: Callable[[str | None], None],
        file_types: list[tuple[str, list[str]]] = [],
        directory: Optional[str] = None,
        name: Optional[str] = None,
        extension: Optional[str] = None):
    """
    Show the save file dialog

    .. since:: 4075

    :param callback: Called with selected path or ``None`` once the dialog is closed.
    :param file_types: A list of allowed file types, consisting of a description
                       and a list of allowed extensions.
    :param directory: The directory the dialog should start in.  Will use the
                      virtual working directory if not provided.
    :param name: The default name of the file in the save dialog.
    :param extension: The default extension used in the save dialog.
    """
    sublime_api.save_dialog(file_types, directory or '', name or '', extension or '', callback)


def select_folder_dialog(
        callback: Callable[[str | list[str] | None], None],
        directory: Optional[str] = None,
        multi_select=False):
    """
    Show the select folder dialog.

    .. since:: 4075

    :param callback: Called with selected path(s) or ``None`` once the dialog is closed.
    :param directory: The directory the dialog should start in.  Will use the
                      virtual working directory if not provided.
    :param multi_select: Whether to allow selecting multiple files. When ``True``
                         the callback will be called with a list.
    """
    cb = callback
    if not multi_select:
        cb = lambda folders: callback(folders[0] if folders else None)

    sublime_api.select_folder_dialog(directory or '', multi_select, cb)


def run_command(cmd: str, args: CommandArgs = None):
    """
    Run the named `ApplicationCommand`.
    """
    sublime_api.run_command(cmd, args)


def format_command(cmd: str, args: CommandArgs = None) -> str:
    """
    Create a "command string" from a ``cmd`` name and ``args`` arguments. This
    is used when constructing a command-based `CompletionItem`.

    .. since:: 4075
    """
    if args is None:
        return cmd
    else:
        arg_str = json.dumps(
            args,
            ensure_ascii=False,
            check_circular=False,
            separators=(',', ':')
        )
        return f'{cmd} {arg_str}'


def html_format_command(cmd: str, args: CommandArgs = None) -> str:
    """
    :returns: An escaped "command string" for usage in HTML popups and sheets.

    .. since:: 4075
    """
    return html.escape(format_command(cmd, args), quote=True)


def command_url(cmd: str, args: CommandArgs = None) -> str:
    """
    :returns: A HTML embeddable URL for a command.

    .. since:: 4075
    """
    return f'subl:{html_format_command(cmd, args)}'


def get_clipboard_async(callback: Callable[[str], None], size_limit: int = 16777216):
    """
    Get the contents of the clipboard in a callback.

    For performance reasons if the size of the clipboard content is bigger than
    ``size_limit``, an empty string will be passed to the callback.

    .. since:: 4075
    """
    sublime_api.get_clipboard_async(callback, size_limit)


def get_clipboard(size_limit: int = 16777216) -> str:
    """
    Get the contents of the clipboard.

    For performance reasons if the size of the clipboard content is bigger than
    ``size_limit``, an empty string will be returned.

    :deprecated: Use `get_clipboard_async` instead. :since:`4075`
    """
    return sublime_api.get_clipboard(size_limit)


def set_clipboard(text: str):
    """ Set the contents of the clipboard. """
    sublime_api.set_clipboard(text)


def log_commands(flag: Optional[bool] = None):
    """
    Control whether commands are logged to the console when run.

    :param flag: Whether to log. :since:`Passing None toggles logging. <4099>`
    """
    if flag is None:
        flag = not get_log_commands()
    sublime_api.log_commands(flag)


def get_log_commands() -> bool:
    """
    Get whether command logging is enabled.

    .. since:: 4099
    """
    return sublime_api.get_log_commands()


def log_input(flag: Optional[bool] = None):
    """
    Control whether all key presses will be logged to the console. Use this to
    find the names of certain keys on the keyboard.

    :param flag: Whether to log. :since:`Passing None toggles logging. <4099>`
    """
    if flag is None:
        flag = not get_log_input()
    sublime_api.log_input(flag)


def get_log_input() -> bool:
    """
    Get whether input logging is enabled.

    .. since:: 4099
    """
    return sublime_api.get_log_input()


def log_fps(flag: Optional[bool] = None):
    """
    Control whether rendering timings like frames per second get logged.

    .. since:: 4099

    :param flag: Whether to log. Pass ``None`` to toggle logging.
    """
    if flag is None:
        flag = not get_log_fps()
    sublime_api.log_fps(flag)


def get_log_fps() -> bool:
    """
    Get whether fps logging is enabled.

    .. since:: 4099
    """
    return sublime_api.get_log_fps()


def log_result_regex(flag: Optional[bool] = None):
    """
    Control whether result regex logging is enabled. Use this to debug
    ``"file_regex"`` and ``"line_regex"`` in build systems.

    :param flag: Whether to log. :since:`Passing None toggles logging. <4099>`
    """
    if flag is None:
        flag = not get_log_result_regex()
    sublime_api.log_result_regex(flag)


def get_log_result_regex() -> bool:
    """
    Get whether result regex logging is enabled.

    .. since:: 4099
    """
    return sublime_api.get_log_result_regex()


def log_indexing(flag: Optional[bool] = None):
    """
    Control whether indexing logs are printed to the console.

    :param flag: Whether to log. :since:`Passing None toggles logging. <4099>`
    """
    if flag is None:
        flag = not get_log_indexing()
    sublime_api.log_indexing(flag)


def get_log_indexing() -> bool:
    """
    Get whether indexing logging is enabled.

    .. since:: 4099
    """
    return sublime_api.get_log_indexing()


def log_build_systems(flag: Optional[bool] = None):
    """
    Control whether build system logs are printed to the console.

    :param flag: Whether to log. :since:`Passing None toggles logging. <4099>`
    """
    if flag is None:
        flag = not get_log_build_systems()
    sublime_api.log_build_systems(flag)


def get_log_build_systems() -> bool:
    """
    Get whether build system logging is enabled.

    .. since:: 4099
    """
    return sublime_api.get_log_build_systems()


def log_control_tree(flag: Optional[bool] = None):
    """
    Control whether control tree logging is enabled. When enabled clicking with
    ctrl+alt will log the control tree under the mouse to the console.

    .. since:: 4064

    :param flag: Whether to log. :since:`Passing None toggles logging. <4099>`
    """
    if flag is None:
        flag = not get_log_control_tree()
    sublime_api.log_control_tree(flag)


def get_log_control_tree() -> bool:
    """
    Get whether control tree logging is enabled.

    .. since:: 4099
    """
    return sublime_api.get_log_control_tree()


def ui_info() -> dict:
    """
    .. since:: 4096

    :returns: Information about the user interface including top-level keys
              ``system``, ``theme`` and ``color_scheme``.
    """
    return sublime_api.ui_info()


def score_selector(scope_name: str, selector: str) -> int:
    """
    Match the ``selector`` against the given ``scope_name``, returning a score for how well they match.

    A score of ``0`` means no match, above ``0`` means a match. Different
    selectors may be compared against the same scope: a higher score means the
    selector is a better match for the scope.
    """
    return sublime_api.score_selector(scope_name, selector)


def load_resource(name: str) -> str:
    """
    Loads the given resource. The name should be in the format "Packages/Default/Main.sublime-menu".

    :raises FileNotFoundError: if resource is not found
    """
    s = sublime_api.load_resource(name)
    if s is None:
        raise FileNotFoundError(f'resource "{name}" not found')
    return s


def load_binary_resource(name) -> bytes:
    """
    Loads the given resource. The name should be in the format "Packages/Default/Main.sublime-menu".

    :raises FileNotFoundError: if resource is not found
    """
    bytes = sublime_api.load_binary_resource(name)
    if bytes is None:
        raise FileNotFoundError(f'resource "{name}" not found')
    return bytes


def find_resources(pattern: str) -> list[str]:
    """
    Finds resources whose file name matches the given glob pattern.
    """
    return sublime_api.find_resources(pattern)


def encode_value(value: Value, pretty=False) -> str:
    """
    Encode a JSON compatible `Value` into a string representation.

    :param pretty: Whether the result should include newlines and be indented.
    """
    return sublime_api.encode_value(value, pretty)


def decode_value(data: str) -> Value:
    """
    Decode a JSON string into an object. Note that comments and trailing commas
    are allowed.

    :raises ValueError: If the string is not valid JSON.
    """
    value, err = sublime_api.decode_value(data)

    if err:
        raise ValueError(err)

    return value


def expand_variables(value: Value, variables: dict[str, str]) -> Value:
    """
    Expands any variables in ``value`` using the variables defined in the
    dictionary ``variables``. value may also be a list or dict, in which case the
    structure will be recursively expanded. Strings should use snippet syntax,
    for example: ``expand_variables("Hello, ${name}", {"name": "Foo"})``.
    """
    return sublime_api.expand_variables(value, variables)


def load_settings(base_name: str) -> Settings:
    """
    Loads the named settings. The name should include a file name and extension,
    but not a path. The packages will be searched for files matching the
    base_name, and the results will be collated into the settings object.

    Subsequent calls to load_settings() with the base_name will return the same
    object, and not load the settings from disk again.
    """
    settings_id = sublime_api.load_settings(base_name)
    return Settings(settings_id)


def save_settings(base_name: str):
    """
    Flush any in-memory changes to the named settings object to disk.
    """
    sublime_api.save_settings(base_name)


def set_timeout(callback: Callable, delay: int = 0):
    """
    Run the ``callback`` in the main thread after the given ``delay``
    (in milliseconds). Callbacks with an equal delay will be run in the order
    they were added.
    """
    sublime_api.set_timeout(callback, delay)


def set_timeout_async(callback: Callable, delay: int = 0):
    """
    Runs the callback on an alternate thread after the given delay
    (in milliseconds).
    """
    sublime_api.set_timeout_async(callback, delay)


def active_window() -> Window:
    """
    :returns: The most recently used `Window`.
    """
    return Window(sublime_api.active_window())


def windows() -> list[Window]:
    """
    :returns: A list of all the open windows.
    """
    return [Window(id) for id in sublime_api.windows()]


def get_macro() -> list[dict]:
    """
    :returns: A list of the commands and args that compromise the currently
              recorded macro. Each ``dict`` will contain the keys ``"command"``
              and ``"args"``.
    """
    return sublime_api.get_macro()


class Window:
    """
    """

    def __init__(self, id: int):
        self.window_id = id
        self.settings_object: Optional[Settings] = None
        self.template_settings_object: Optional[Settings] = None

    def __hash__(self) -> int:
        return self.window_id

    def __eq__(self, other):
        return isinstance(other, Window) and other.window_id == self.window_id

    def __bool__(self) -> bool:
        return self.window_id != 0

    def __repr__(self) -> str:
        return f'Window({self.window_id!r})'

    def id(self) -> int:
        """
        :returns: A number that uniquely identifies this window.
        """
        return self.window_id

    def is_valid(self) -> bool:
        """
        Check whether this window is still valid. Will return ``False`` for a
        closed window, for example.
        """
        return sublime_api.window_num_groups(self.window_id) != 0

    def hwnd(self) -> int:
        """
        :returns: A platform specific window handle. Windows only.
        """
        return sublime_api.window_system_handle(self.window_id)

    def active_sheet(self) -> Optional[Sheet]:
        """
        :returns: The currently focused `Sheet`.
        """
        sheet_id = sublime_api.window_active_sheet(self.window_id)
        if sheet_id == 0:
            return None
        else:
            return make_sheet(sheet_id)

    def active_view(self) -> Optional[View]:
        """
        :returns: The currently edited `View`.
        """
        view_id = sublime_api.window_active_view(self.window_id)
        if view_id == 0:
            return None
        else:
            return View(view_id)

    def new_html_sheet(self, name: str, contents: str, flags=NewFileFlags.NONE, group=-1) -> Sheet:
        """
        Construct a sheet with HTML contents rendered using `minihtml`.

        .. since:: 4065

        :param name: The name of the sheet to show in the tab.
        :param contents: The HTML contents of the sheet.
        :param flags: Only `NewFileFlags.TRANSIENT` and
                      `NewFileFlags.ADD_TO_SELECTION` are allowed.
        :param group: The group to add the sheet to. ``-1`` for the active group.
        """
        return make_sheet(sublime_api.window_new_html_sheet(
            self.window_id, name, contents, flags, group))

    def run_command(self, cmd: str, args: CommandArgs = None):
        """
        Run the named `WindowCommand` with the (optional) given args. This
        method is able to run any sort of command, dispatching the command via
        input focus.
        """
        sublime_api.window_run_command(self.window_id, cmd, args)

    def new_file(self, flags=NewFileFlags.NONE, syntax="") -> View:
        """
        Create a new empty file.

        :param flags: Either ``0``, `NewFileFlags.TRANSIENT` or `NewFileFlags.ADD_TO_SELECTION`.
        :param syntax: The name of the syntax to apply to the file.
        :returns: The view for the file.
        """
        return View(sublime_api.window_new_file(self.window_id, flags, syntax))

    def open_file(self, fname: str, flags=NewFileFlags.NONE, group=-1) -> View:
        """
        Open the named file. If the file is already opened, it will be brought
        to the front. Note that as file loading is asynchronous, operations on
        the returned view won't be possible until its ``is_loading()`` method
        returns ``False``.

        :param fname: The path to the file to open.
        :param flags: `NewFileFlags`
        :param group: The group to add the sheet to. ``-1`` for the active group.
        """
        return View(sublime_api.window_open_file(self.window_id, fname, flags, group))

    def find_open_file(self, fname: str, group=-1) -> Optional[View]:
        """
        Find a opened file by file name.

        :param fname: The path to the file to open.
        :param group: The group in which to search for the file. ``-1`` for any group.

        :returns: The `View` to the file or ``None`` if the file isn't open.
        """
        view_id = sublime_api.window_find_open_file(self.window_id, fname, group)
        if view_id == 0:
            return None
        else:
            return View(view_id)

    def file_history(self) -> list[str]:
        """
        Get the list of previously opened files. This is the same list
        as *File > Open Recent*.
        """
        return sublime_api.window_file_history(self.window_id)

    def num_groups(self) -> int:
        """
        :returns: The number of view groups in the window.
        """
        return sublime_api.window_num_groups(self.window_id)

    def active_group(self) -> int:
        """
        :returns: The index of the currently selected group.
        """
        return sublime_api.window_active_group(self.window_id)

    def focus_group(self, idx: int):
        """
        Focus the specified group, making it active.
        """
        sublime_api.window_focus_group(self.window_id, idx)

    def focus_sheet(self, sheet: Sheet):
        """
        Switches to the given `Sheet`.
        """
        if sheet:
            sublime_api.window_focus_sheet(self.window_id, sheet.sheet_id)

    def focus_view(self, view: View):
        """
        Switches to the given `View`.
        """
        if view:
            sublime_api.window_focus_view(self.window_id, view.view_id)

    def select_sheets(self, sheets: list[Sheet]):
        """
        Change the selected sheets for the entire window.

        .. since:: 4083
        """
        sublime_api.window_select_sheets(self.window_id, [s.sheet_id for s in sheets])

    def bring_to_front(self):
        """
        Bring the window in front of any other windows.
        """
        sublime_api.window_bring_to_front(self.window_id)

    def get_sheet_index(self, sheet: Sheet) -> tuple[int, int]:
        """
        :returns: The a tuple of the group and index within the group of the
                  given `Sheet`.
        """
        if sheet:
            return sublime_api.window_get_sheet_index(self.window_id, sheet.sheet_id)
        else:
            return (-1, -1)

    def get_view_index(self, view: View) -> tuple[int, int]:
        """
        :returns: The a tuple of the group and index within the group of the
                  given `View`.
        """
        if view:
            return sublime_api.window_get_view_index(self.window_id, view.view_id)
        else:
            return (-1, -1)

    def set_sheet_index(self, sheet: Sheet, group: int, index: int):
        """
        Move the given `Sheet` to the given ``group`` at the given ``index``.
        """
        sublime_api.window_set_sheet_index(self.window_id, sheet.sheet_id, group, index)

    def set_view_index(self, view: View, group: int, index: int):
        """
        Move the given `View` to the given ``group`` at the given ``index``.
        """
        sublime_api.window_set_view_index(self.window_id, view.view_id, group, index)

    def move_sheets_to_group(self, sheets: list[Sheet], group: int, insertion_idx=-1, select=True):
        """
        Moves all provided sheets to specified group at insertion index
        provided. If an index is not provided defaults to last index of the
        destination group.

        .. since:: 4123

        :param sheets: The sheets to move.
        :param group: The index of the group to move the sheets to.
        :param insertion_idx: The point inside the group at which to insert the sheets.
        :param select: Whether the sheets should be selected after moving them.

        """
        sheet_ids = []
        for sheet in sheets:
            if not isinstance(sheet, Sheet):
                raise TypeError('list must contain items of type sublime.Sheet only')
            sheet_ids.append(sheet.id())
        sublime_api.window_move_sheets_to_group(self.window_id, sheet_ids, group, insertion_idx, select)

    def sheets(self) -> list[Sheet]:
        """
        :returns: All open sheets in the window.
        """
        sheet_ids = sublime_api.window_sheets(self.window_id)
        return [make_sheet(x) for x in sheet_ids]

    def views(self, *, include_transient=False) -> list[View]:
        """
        :param include_transient: Whether the transient sheet should be included.

            .. since:: 4081
        :returns: All open sheets in the window.
        """
        view_ids = sublime_api.window_views(self.window_id, include_transient)
        return [View(x) for x in view_ids]

    def selected_sheets(self) -> list[Sheet]:
        """
        .. since:: 4083

        :returns: All selected sheets in the window.
        """
        sheet_ids = sublime_api.window_selected_sheets(self.window_id)
        return [make_sheet(s) for s in sheet_ids]

    def selected_sheets_in_group(self, group: int) -> list[Sheet]:
        """
        .. since:: 4083

        :returns: All selected sheets in the specified group.
        """
        sheet_ids = sublime_api.window_selected_sheets_in_group(self.window_id, group)
        return [make_sheet(s) for s in sheet_ids]

    def active_sheet_in_group(self, group: int) -> Optional[Sheet]:
        """
        :returns: The currently focused `Sheet` in the given group.
        """
        sheet_id = sublime_api.window_active_sheet_in_group(self.window_id, group)
        if sheet_id == 0:
            return None
        else:
            return make_sheet(sheet_id)

    def active_view_in_group(self, group: int) -> Optional[View]:
        """
        :returns: The currently focused `View` in the given group.
        """
        view_id = sublime_api.window_active_view_in_group(self.window_id, group)
        if view_id == 0:
            return None
        else:
            return View(view_id)

    def sheets_in_group(self, group: int) -> list[Sheet]:
        """
        :returns: A list of all sheets in the specified group.
        """
        sheet_ids = sublime_api.window_sheets_in_group(self.window_id, group)
        return [make_sheet(x) for x in sheet_ids]

    def views_in_group(self, group: int) -> list[View]:
        """
        :returns: A list of all views in the specified group.
        """
        view_ids = sublime_api.window_views_in_group(self.window_id, group)
        return [View(x) for x in view_ids]

    def transient_sheet_in_group(self, group: int) -> Optional[Sheet]:
        """
        :returns: The transient sheet in the specified group.
        """
        sheet_id = sublime_api.window_transient_sheet_in_group(self.window_id, group)
        if sheet_id != 0:
            return make_sheet(sheet_id)
        else:
            return None

    def transient_view_in_group(self, group: int) -> Optional[View]:
        """
        :returns: The transient view in the specified group.
        """
        view_id = sublime_api.window_transient_view_in_group(self.window_id, group)
        if view_id != 0:
            return View(view_id)
        else:
            return None

    def promote_sheet(self, sheet: Sheet):
        """
        Promote the 'Sheet' parameter if semi-transient or transient.

        :since: next
        """
        sublime_api.window_promote_sheet(self.window_id, sheet.id())

    def layout(self) -> dict[str, Value]:
        """
        Get the group layout of the window.
        """
        return sublime_api.window_get_layout(self.window_id)

    def get_layout(self):
        """
        :deprecated: Use `layout()` instead
        """
        return sublime_api.window_get_layout(self.window_id)

    def set_layout(self, layout: dict[str, Value]):
        """
        Set the group layout of the window.
        """
        sublime_api.window_set_layout(self.window_id, layout)

    def create_output_panel(self, name: str, unlisted=False) -> View:
        """
        Find the view associated with the named output panel, creating it if
        required. The output panel can be shown by running the ``show_panel``
        window command, with the ``panel`` argument set to the name with
        an ``"output."`` prefix.

        The optional ``unlisted`` parameter is a boolean to control if the output
        panel should be listed in the panel switcher.
        """
        return View(sublime_api.window_create_output_panel(self.window_id, name, unlisted))

    def find_output_panel(self, name: str) -> Optional[View]:
        """
        :returns:
            The `View` associated with the named output panel, or ``None`` if
            the output panel does not exist.
        """
        view_id = sublime_api.window_find_output_panel(self.window_id, name)
        return View(view_id) if view_id else None

    def destroy_output_panel(self, name: str):
        """
        Destroy the named output panel, hiding it if currently open.
        """
        sublime_api.window_destroy_output_panel(self.window_id, name)

    def active_panel(self) -> Optional[str]:
        """
        Returns the name of the currently open panel, or None if no panel is
        open. Will return built-in panel names (e.g. ``"console"``, ``"find"``,
        etc) in addition to output panels.
        """
        name = sublime_api.window_active_panel(self.window_id)
        return name or None

    def panels(self) -> list[str]:
        """
        Returns a list of the names of all panels that have not been marked as
        unlisted. Includes certain built-in panels in addition to output
        panels.
        """
        return sublime_api.window_panels(self.window_id)

    def get_output_panel(self, name: str):
        """ :deprecated: Use `create_output_panel` instead. """
        return self.create_output_panel(name)

    def show_input_panel(self, caption: str, initial_text: str,
                         on_done: Optional[Callable[[str], None]],
                         on_change: Optional[Callable[[str], None]],
                         on_cancel: Optional[Callable[[], None]]):
        """
        Shows the input panel, to collect a line of input from the user.

        :param caption: The label to put next to the input widget.
        :param initial_text: The initial text inside the input widget.
        :param on_done: Called with the final input when the user presses ``enter``.
        :param on_change: Called with the input when it's changed.
        :param on_cancel: Called when the user cancels input using ``esc``
        :returns: The `View` used for the input widget.
        """
        return View(sublime_api.window_show_input_panel(
            self.window_id, caption, initial_text, on_done, on_change, on_cancel))

    def show_quick_panel(self,
                         items: list[str] | list[list[str]] | list[QuickPanelItem],
                         on_select: Callable[[int], None],
                         flags=QuickPanelFlags.NONE,
                         selected_index=-1,
                         on_highlight: Optional[Callable[[int], None]] = None,
                         placeholder: Optional[str] = None):
        """
        Show a quick panel to select an item in a list. on_select will be called
        once, with the index of the selected item. If the quick panel was
        cancelled, on_select will be called with an argument of -1.

        :param items:
            May be either a list of strings, or a list of lists of strings where
            the first item is the trigger and all subsequent strings are
            details shown below.

            .. since:: 4083
                May be a `QuickPanelItem`.
        :param on_select:
            Called with the selected item's index when the quick panel is
            completed. If the panel was cancelled this is called with ``-1``.

            .. since:: 4096
                A second `Event` argument may be passed when the
                `QuickPanelFlags.WANT_EVENT` flag is present.
        :param flags: `QuickPanelFlags` controlling behavior.
        :param selected_index: The initially selected item. ``-1`` for no selection.
        :param on_highlight:
            Called every time the highlighted item in the quick panel is changed.
        :param placeholder:
            Text displayed in the filter input field before any query is typed.
            :since:`4081`
        """

        item_tuples: list[str | tuple | QuickPanelItem] = []
        if len(items) > 0:
            for item in items:
                if isinstance(item, str):
                    item_tuples.append(item)
                elif isinstance(item, (list, tuple)):
                    item_tuples.append((item[0], "\x1f".join(item[1:])))
                elif isinstance(item, QuickPanelItem):
                    details = "\x1f".join(item.details) if isinstance(item.details, (list, tuple)) else item.details
                    if item.annotation != "" or item.kind != (KIND_ID_AMBIGUOUS, "", ""):
                        kind_letter = 0
                        if isinstance(item.kind[1], str) and len(item.kind[1]) == 1:
                            kind_letter = ord(item.kind[1])
                        item_tuples.append((
                            item.trigger,
                            details,
                            item.annotation,
                            (item.kind[0], kind_letter, item.kind[2])
                        ))
                    elif details is not None and details != "":
                        item_tuples.append((item.trigger, details, True))
                    else:
                        item_tuples.append(item.trigger)
                else:
                    raise TypeError("items must contain only str, list, tuple or QuickPanelItem objects")

        sublime_api.window_show_quick_panel(
            self.window_id, item_tuples, on_select, on_highlight,
            flags, selected_index, placeholder or '')

    def is_sidebar_visible(self) -> bool:
        """ :returns: Whether the sidebar is visible. """
        return sublime_api.window_is_ui_element_visible(self.window_id, UIElement.SIDE_BAR)

    def set_sidebar_visible(self, flag: bool):
        """ Hides or shows the sidebar. """
        sublime_api.window_set_ui_element_visible(self.window_id, UIElement.SIDE_BAR, flag)

    def is_minimap_visible(self) -> bool:
        """ :returns: Whether the minimap is visible. """
        return sublime_api.window_is_ui_element_visible(self.window_id, UIElement.MINIMAP)

    def set_minimap_visible(self, flag: bool):
        """ Hides or shows the minimap. """
        sublime_api.window_set_ui_element_visible(self.window_id, UIElement.MINIMAP, flag)

    def is_status_bar_visible(self) -> bool:
        """ :returns: Whether the status bar is visible. """
        return sublime_api.window_is_ui_element_visible(self.window_id, UIElement.STATUS_BAR)

    def set_status_bar_visible(self, flag: bool):
        """ Hides or shows the status bar. """
        sublime_api.window_set_ui_element_visible(self.window_id, UIElement.STATUS_BAR, flag)

    def get_tabs_visible(self) -> bool:
        """ :returns: Whether the tabs are visible. """
        return sublime_api.window_is_ui_element_visible(self.window_id, UIElement.TABS)

    def set_tabs_visible(self, flag: bool):
        """ Hides or shows the tabs. """
        sublime_api.window_set_ui_element_visible(self.window_id, UIElement.TABS, flag)

    def is_menu_visible(self) -> bool:
        """ :returns: Whether the menu is visible. """
        return sublime_api.window_is_ui_element_visible(self.window_id, UIElement.MENU)

    def set_menu_visible(self, flag: bool):
        """ Hides or shows the menu. """
        sublime_api.window_set_ui_element_visible(self.window_id, UIElement.MENU, flag)

    def folders(self) -> list[str]:
        """ :returns: A list of the currently open folders in this `Window`. """
        return sublime_api.window_folders(self.window_id)

    def project_file_name(self) -> Optional[str]:
        """ :returns: The name of the currently opened project file, if any. """
        name = sublime_api.window_project_file_name(self.window_id)
        if len(name) == 0:
            return None
        else:
            return name

    def workspace_file_name(self) -> Optional[str]:
        """
        .. since:: 4050

        :returns: The name of the currently opened workspace file, if any.
        """
        name = sublime_api.window_workspace_file_name(self.window_id)
        if len(name) == 0:
            return None
        return name

    def project_data(self) -> Value:
        """
        :returns: The project data associated with the current window. The data
                  is in the same format as the contents of a
                  :path:`.sublime-project` file.
        """
        return sublime_api.window_get_project_data(self.window_id)

    def set_project_data(self, data: Value):
        """
        Updates the project data associated with the current window. If the
        window is associated with a :path:`.sublime-project` file, the project
        file will be updated on disk, otherwise the window will store the data
        internally.
        """
        sublime_api.window_set_project_data(self.window_id, data)

    def settings(self) -> Settings:
        """
        :returns: The `Settings` object for this `Window`. Any changes to this
                  settings object will be specific to this window.
        """
        if not self.settings_object:
            self.settings_object = Settings(
                sublime_api.window_settings(self.window_id))

        return self.settings_object

    def template_settings(self) -> Settings:
        """
        :returns: Per-window settings that are persisted in the session, and
                  duplicated into new windows.
        """
        if not self.template_settings_object:
            self.template_settings_object = Settings(
                sublime_api.window_template_settings(self.window_id))

        return self.template_settings_object

    def symbol_locations(self,
                         sym: str,
                         source=SymbolSource.ANY,
                         type=SymbolType.ANY,
                         kind_id=KindId.AMBIGUOUS,
                         kind_letter='') -> list[SymbolLocation]:
        """
        Find all locations where the symbol ``sym`` is located.

        .. since:: 4085

        :param sym: The name of the symbol.
        :param source: Sources which should be searched for the symbol.
        :param type: The type of symbol to find
        :param kind_id: The `KindId` of the symbol.
        :param kind_letter: The letter representing the kind of the symbol. See `Kind`.
        :return: the found symbol locations.
        """

        letter = 0
        if not isinstance(kind_letter, str):
            kind_letter = ''
        if len(kind_letter) > 0:
            letter = ord(kind_letter)

        return sublime_api.window_symbol_locations(self.window_id, sym, source, type, kind_id, letter)

    def lookup_symbol_in_index(self, symbol: str) -> list[SymbolLocation]:
        """
        :returns: All locations where the symbol is defined across files in the current project.
        :deprecated: Use `symbol_locations()` instead.
        """
        return sublime_api.window_lookup_symbol(self.window_id, symbol)

    def lookup_symbol_in_open_files(self, symbol: str) -> list[SymbolLocation]:
        """
        :returns: All locations where the symbol is defined across open files.
        :deprecated: Use `symbol_locations()` instead.
        """
        return sublime_api.window_lookup_symbol_in_open_files(self.window_id, symbol)

    def lookup_references_in_index(self, symbol: str) -> list[SymbolLocation]:
        """
        :returns: All locations where the symbol is referenced across files in the current project.
        :deprecated: Use `symbol_locations()` instead.
        """
        return sublime_api.window_lookup_references(self.window_id, symbol)

    def lookup_references_in_open_files(self, symbol: str) -> list[SymbolLocation]:
        """
        :returns: All locations where the symbol is referenced across open files.
        :deprecated: Use `symbol_locations()` instead.
        """
        return sublime_api.window_lookup_references_in_open_files(self.window_id, symbol)

    def extract_variables(self) -> dict[str, str]:
        """
        Get the ``dict`` of contextual keys of the window.

        May contain:
        * ``"packages"``
        * ``"platform"``
        * ``"file"``
        * ``"file_path"``
        * ``"file_name"``
        * ``"file_base_name"``
        * ``"file_extension"``
        * ``"folder"``
        * ``"project"``
        * ``"project_path"``
        * ``"project_name"``
        * ``"project_base_name"``
        * ``"project_extension"``

        This ``dict`` is suitable for use with `expand_variables()`.
        """
        return sublime_api.window_extract_variables(self.window_id)

    def status_message(self, msg: str):
        """ Show a message in the status bar. """
        sublime_api.window_status_message(self.window_id, msg)


class Edit:
    """
    A grouping of buffer modifications.

    Edit objects are passed to `TextCommand`\\ s, and can not be created by the
    user. Using an invalid Edit object, or an Edit object from a different
    `View`, will cause the functions that require them to fail.
    """

    def __init__(self, token):
        self.edit_token: int = token

    def __repr__(self) -> str:
        return f'Edit({self.edit_token!r})'


class Region:
    """
    A singular selection region. This region has a order - ``b`` may be before
    or at ``a``.

    Also commonly used to represent an area of the text buffer, where ordering
    and ``xpos`` are generally ignored.
    """

    __slots__ = ['a', 'b', 'xpos']

    def __init__(self, a: Point, b: Optional[Point] = None, xpos: DIP = -1):
        """ """
        if b is None:
            b = a

        self.a: Point = a
        """ The first end of the region. """
        self.b: Point = b
        """
        The second end of the region. In a selection this is the location of the
        caret. May be less than ``a``.
        """
        self.xpos: DIP = xpos
        """
        In a selection this is the target horizontal position of the region.
        This affects behavior when pressing the up or down keys. Use ``-1`` if
        undefined.
        """

    def __iter__(self):
        """
        Iterate through all the points in the region.

        .. since:: 4023 3.8
        """
        return iter((self.a, self.b))

    def __str__(self) -> str:
        return "(" + str(self.a) + ", " + str(self.b) + ")"

    def __repr__(self) -> str:
        if self.xpos == -1:
            return f'Region({self.a}, {self.b})'
        return f'Region({self.a}, {self.b}, xpos={self.xpos})'

    def __len__(self) -> int:
        """ :returns: The size of the region. """
        return self.size()

    def __eq__(self, rhs: object) -> bool:
        """
        :returns: Whether the two regions are identical. Ignores ``xpos``.
        """
        return isinstance(rhs, Region) and self.a == rhs.a and self.b == rhs.b

    def __lt__(self, rhs: Region) -> bool:
        """
        :returns: Whether this region starts before the rhs. The end of the
                  region is used to resolve ties.
        """
        lhs_begin = self.begin()
        rhs_begin = rhs.begin()

        if lhs_begin == rhs_begin:
            return self.end() < rhs.end()
        else:
            return lhs_begin < rhs_begin

    def __contains__(self, v: Region | Point) -> bool:
        """
        :returns: Whether the provided `Region` or `Point` is entirely contained
                  within this region.

        .. since:: 4023 3.8
        """
        if isinstance(v, Region):
            return v.a in self and v.b in self
        elif isinstance(v, int):
            return v >= self.begin() and v <= self.end()
        else:
            fq_name = ""
            if v.__class__.__module__ not in {'builtins', '__builtin__'}:
                fq_name = f"{v.__class__.__module__}."
            fq_name += v.__class__.__qualname__
            raise TypeError(
                "in <Region> requires int or Region as left operand"
                f", not {fq_name}")

    def to_tuple(self) -> tuple[Point, Point]:
        """
        .. since:: 4075

        :returns: This region as a tuple ``(a, b)``.
        """
        return (self.a, self.b)

    def empty(self) -> bool:
        """ :returns: Whether the region is empty, ie. ``a == b``. """
        return self.a == self.b

    def begin(self) -> Point:
        """ :returns: The smaller of ``a`` and ``b``. """
        if self.a < self.b:
            return self.a
        else:
            return self.b

    def end(self) -> Point:
        """ :returns: The larger of ``a`` and ``b``. """
        if self.a < self.b:
            return self.b
        else:
            return self.a

    def size(self) -> int:
        """ Equivalent to `__len__`. """
        return abs(self.a - self.b)

    def contains(self, x: Point) -> bool:
        """ Equivalent to `__contains__`. """
        return x in self

    def cover(self, region: Region) -> Region:
        """ :returns: A `Region` spanning both regions. """
        a = min(self.begin(), region.begin())
        b = max(self.end(), region.end())

        if self.a < self.b:
            return Region(a, b)
        else:
            return Region(b, a)

    def intersection(self, region: Region) -> Region:
        """ :returns: A `Region` covered by both regions. """
        if self.end() <= region.begin():
            return Region(0)
        if self.begin() >= region.end():
            return Region(0)

        return Region(max(self.begin(), region.begin()), min(self.end(), region.end()))

    def intersects(self, region: Region) -> bool:
        """ :returns: Whether the provided region intersects this region. """
        lb = self.begin()
        le = self.end()
        rb = region.begin()
        re = region.end()

        return (
            (lb == rb and le == re) or
            (rb > lb and rb < le) or (re > lb and re < le) or
            (lb > rb and lb < re) or (le > rb and le < re))


class HistoricPosition:
    """
    Provides a snapshot of the row and column info for a `Point`, before changes
    were made to a `View`. This is primarily useful for replaying changes to a
    document.

    .. since:: 4050
    """

    __slots__ = ['pt', 'row', 'col', 'col_utf16', 'col_utf8']

    def __init__(self, pt, row, col, col_utf16, col_utf8):
        self.pt: Point = pt
        """ The offset from the beginning of the `View`. """
        self.row: int = row
        """ The row the ``.py`` was in when the `HistoricPosition` was recorded. """
        self.col: int = col
        """ The column the ``.py`` was in when the `HistoricPosition` was recorded, in Unicode characters. """
        self.col_utf16: int = col_utf16
        """
        The value of ``.col``, but in UTF-16 code units.

        .. since:: 4075
        """
        self.col_utf8: int = col_utf8
        """
        The value of ``.col``, but in UTF-8 code units.

        .. since:: 4075
        """

    def __repr__(self):
        return (f'HistoricPosition(pt={self.pt!r}, row={self.row!r}, '
                f'col={self.col!r}, col_utf16={self.col_utf16!r}, '
                f'col_utf8={self.col_utf8!r})')


class TextChange:
    """
    Represents a change that occurred to the text of a `View`. This is primarily
    useful for replaying changes to a document.

    .. since:: 4050
    """

    __slots__ = ['a', 'b', 'len_utf16', 'len_utf8', 'str']

    def __init__(self, pa, pb, len_utf16, len_utf8, str):
        self.a: HistoricPosition = pa
        """ The beginning `HistoricPosition` of the region that was modified. """
        self.b: HistoricPosition = pb
        """ The ending `HistoricPosition` of the region that was modified. """
        self.len_utf16: int = len_utf16
        """
        The length of the old contents, in UTF-16 code units.

        .. since:: 4075
        """
        self.len_utf8: int = len_utf8
        """
        The length of the old contents, in UTF-8 code units.

        .. since:: 4075
        """
        self.str: str = str
        """
        A string of the *new* contents of the region specified by ``.a`` and ``.b``.

        :meta noindex:
        """

    def __repr__(self):
        return (f'TextChange({self.a!r}, {self.b!r}, '
                f'len_utf16={self.len_utf16!r}, len_utf8={self.len_utf8!r}, '
                f'str={self.str!r})')


class Selection:
    """
    Maintains a set of sorted non-overlapping Regions. A selection may be
    empty.

    This is primarily used to represent the textual selection.
    """

    def __init__(self, id):
        self.view_id = id

    def __iter__(self) -> Iterator[Region]:
        """
        Iterate through all the regions in the selection.

        .. since:: 4023 3.8
        """
        i = 0
        n = len(self)
        while i < n:
            yield sublime_api.view_selection_get(self.view_id, i)
            i += 1

    def __len__(self) -> int:
        """ :returns: The number of regions in the selection. """
        return sublime_api.view_selection_size(self.view_id)

    def __getitem__(self, index: int) -> Region:
        """ :returns: The region at the given ``index``. """
        r = sublime_api.view_selection_get(self.view_id, index)
        if r.a == -1:
            raise IndexError()
        return r

    def __delitem__(self, index: int):
        """ Delete the region at the given ``index``. """
        sublime_api.view_selection_erase(self.view_id, index)

    def __eq__(self, rhs: object) -> bool:
        """ :returns: Whether the selections are identical. """
        return rhs is not None and isinstance(rhs, Selection) and list(self) == list(rhs)

    def __lt__(self, rhs: Optional[Selection]) -> bool:
        """ """
        return rhs is not None and list(self) < list(rhs)

    def __bool__(self) -> bool:
        """ The selection is ``True`` when not empty. """
        return self.view_id != 0 and len(self) > 0

    def __str__(self) -> str:
        return f"{self!r}[{', '.join(map(str, self))}]"

    def __repr__(self) -> str:
        return f'Selection({self.view_id!r})'

    def is_valid(self) -> bool:
        """ :returns: Whether this selection is for a valid view. """
        return sublime_api.view_buffer_id(self.view_id) != 0

    def clear(self):
        """ Remove all regions from the selection. """
        sublime_api.view_selection_clear(self.view_id)

    def add(self, x: Region | Point):
        """
        Add a `Region` or `Point` to the selection. It will be merged with the
        existing regions if intersecting.
        """
        if isinstance(x, Region):
            sublime_api.view_selection_add_region(self.view_id, x.a, x.b, x.xpos)
        else:
            sublime_api.view_selection_add_point(self.view_id, x)

    def add_all(self, regions: Iterator[Region]):
        """ Add all the regions from the given iterable. """
        for r in regions:
            self.add(r)

    def subtract(self, region: Region):
        """
        Subtract a region from the selection, such that the whole region is no
        longer contained within the selection.
        """
        sublime_api.view_selection_subtract_region(self.view_id, region.a, region.b)

    def contains(self, region: Region) -> bool:
        """ :returns: Whether the provided region is contained within the selection. """
        return sublime_api.view_selection_contains(self.view_id, region.a, region.b)


def make_sheet(sheet_id):
    if (sheet_id & 3) == 0:
        return TextSheet(sheet_id)
    elif (sheet_id & 3) == 1:
        return ImageSheet(sheet_id)
    elif (sheet_id & 3) == 2:
        return HtmlSheet(sheet_id)
    else:
        return None


class Sheet:
    """
    Represents a content container, i.e. a tab, within a window. Sheets may
    contain a View, or an image preview.
    """

    def __init__(self, id):
        self.sheet_id = id

    def __hash__(self) -> int:
        return self.sheet_id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Sheet) and other.sheet_id == self.sheet_id

    def __repr__(self) -> str:
        return f'Sheet({self.sheet_id!r})'

    def id(self) -> int:
        """ :returns: A number that uniquely identifies this sheet. """
        return self.sheet_id

    def window(self) -> Optional[Window]:
        """
        :returns: The `Window` containing this sheet. May be ``None`` if the
                  sheet has been closed.
        """
        window_id = sublime_api.sheet_window(self.sheet_id)
        if window_id == 0:
            return None
        else:
            return Window(window_id)

    def view(self) -> Optional[View]:
        """
        :returns: The `View` contained within the sheet if any.
        """
        view_id = sublime_api.sheet_view(self.sheet_id)
        if view_id == 0:
            return None
        else:
            return View(view_id)

    def file_name(self) -> Optional[str]:
        """
        :returns:
            The full name of the file associated with the sheet, or ``None``
            if it doesn't exist on disk.

        .. since:: 4088
        """
        fn = sublime_api.sheet_file_name(self.sheet_id)
        if len(fn) == 0:
            return None
        return fn

    def is_semi_transient(self) -> bool:
        """
        :returns: Whether this sheet is semi-transient.

        .. since:: 4080
        """
        return sublime_api.sheet_is_semi_transient(self.sheet_id)

    def is_transient(self) -> bool:
        """
        :returns: Whether this sheet is transient.

        .. since:: 4080
        """
        return sublime_api.sheet_is_transient(self.sheet_id)

    def is_selected(self) -> bool:
        """
        :returns: Whether this sheet is currently selected.

        :since: next
        """
        return sublime_api.sheet_is_selected(self.sheet_id)

    def group(self) -> Optional[int]:
        """
        :returns: The (layout) group that the sheet is contained within.

        .. since:: 4100
        """
        group_num = sublime_api.sheet_group(self.sheet_id)
        if group_num == -1:
            return None
        return group_num

    def close(self, on_close=lambda did_close: None):
        """
        Closes the sheet.

        :param on_close:

        .. since:: 4088
        """
        sublime_api.sheet_close(self.sheet_id, on_close)


class TextSheet(Sheet):
    """
    Specialization for sheets containing editable text, ie. a `View`.

    .. since:: 4065
    """

    def __repr__(self):
        return f'TextSheet({self.sheet_id!r})'

    def set_name(self, name: str):
        """ Set the name displayed in the tab. Only affects unsaved files. """
        sublime_api.sheet_set_name(self.sheet_id, name)


class ImageSheet(Sheet):
    """
    Specialization for sheets containing an image.

    .. since:: 4065
    """

    def __repr__(self):
        return f'ImageSheet({self.sheet_id!r})'


class HtmlSheet(Sheet):
    """
    Specialization for sheets containing HTML.

    .. since:: 4065
    """

    def __repr__(self):
        return f'HtmlSheet({self.sheet_id!r})'

    def set_name(self, name: str):
        """ Set the name displayed in the tab. """
        sublime_api.sheet_set_name(self.sheet_id, name)

    def set_contents(self, contents: str):
        """ Set the HTML content of the sheet. """
        sublime_api.html_sheet_set_contents(self.sheet_id, contents)


class ContextStackFrame:
    """
    Represents a single stack frame in the syntax highlighting. See
    `View.context_backtrace`.

    .. since:: 4127
    """

    __slots__ = ['context_name', 'source_file', 'source_location']

    def __init__(self, context_name, source_file, source_location):
        self.context_name: str = context_name
        """ The name of the context. """
        self.source_file: str = source_file
        """ The name of the file the context is defined in. """
        self.source_location: tuple[int, int] = source_location
        """
        The location of the context inside the source file as a pair of row and
        column. Maybe be ``(-1, -1)`` if the location is unclear, like in
        ``tmLanguage`` based syntaxes.
        """

    def __repr__(self) -> str:
        return (f'ContextStackFrame({self.context_name!r},'
                f' {self.source_file!r}, {self.source_location!r})')


class View:
    """
    Represents a view into a text `Buffer`.

    Note that multiple views may refer to the same `Buffer`, but they have their
    own unique selection and geometry. A list of these may be gotten using
    `View.clones()` or `Buffer.views()`.
    """

    def __init__(self, id):
        self.view_id = id
        self.selection = Selection(id)
        self.settings_object = None

    def __len__(self) -> int:
        return self.size()

    def __hash__(self) -> int:
        return self.view_id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, View) and other.view_id == self.view_id

    def __bool__(self) -> bool:
        return self.view_id != 0

    def __repr__(self) -> str:
        return f'View({self.view_id!r})'

    def id(self) -> int:
        """ :returns: A number that uniquely identifies this view. """
        return self.view_id

    def buffer_id(self) -> int:
        """
        :returns: A number that uniquely identifies this view's `Buffer`.
        """
        return sublime_api.view_buffer_id(self.view_id)

    def buffer(self) -> Buffer:
        """ :returns: The `Buffer` for which this is a view. """
        return Buffer(self.buffer_id())

    def sheet_id(self) -> int:
        """
        .. since:: 4083

        :returns:
            The ID of the `Sheet` for this `View`, or ``0`` if not part of any
            sheet.
        """
        return sublime_api.view_sheet_id(self.view_id)

    def sheet(self) -> Optional[Sheet]:
        """
        .. since:: 4083

        :returns: The `Sheet` for this view, if displayed in a sheet.
        """
        return make_sheet(self.sheet_id())

    def element(self) -> Optional[str]:
        """
        .. since:: 4050

        :returns:
            ``None`` for normal views that are part of a `Sheet`. For views that
            comprise part of the UI a string is returned from the following
            list:

            * ``"console:input"`` - The console input.
            * ``"goto_anything:input"`` - The input for the Goto Anything.
            * ``"command_palette:input"`` - The input for the Command Palette.
            * ``"find:input"`` - The input for the Find panel.
            * ``"incremental_find:input"`` - The input for the Incremental Find panel.
            * ``"replace:input:find"`` - The Find input for the Replace panel.
            * ``"replace:input:replace"`` - The Replace input for the Replace panel.
            * ``"find_in_files:input:find"`` - The Find input for the Find in Files panel.
            * ``"find_in_files:input:location"`` - The Where input for the Find in Files panel.
            * ``"find_in_files:input:replace"`` - The Replace input for the Find in Files panel.
            * ``"find_in_files:output"`` - The output panel for Find in Files (buffer or output panel).
            * ``"input:input"`` - The input for the Input panel.
            * ``"exec:output"`` - The output for the exec command.
            * ``"output:output"`` - A general output panel.

            The console output, indexer status output and license input controls
            are not accessible via the API.
        """
        e = sublime_api.view_element(self.view_id)
        if e == "":
            return None
        return e

    def is_valid(self) -> bool:
        """
        Check whether this view is still valid. Will return ``False`` for a
        closed view, for example.
        """
        return sublime_api.view_buffer_id(self.view_id) != 0

    def is_primary(self) -> bool:
        """
        :returns: Whether view is the primary view into a `Buffer`. Will only be
                  ``False`` if the user has opened multiple views into a file.
        """
        return sublime_api.view_is_primary(self.view_id)

    def window(self) -> Optional[Window]:
        """
        :returns: A reference to the window containing the view, if any.
        """
        window_id = sublime_api.view_window(self.view_id)
        if window_id == 0:
            return None
        else:
            return Window(window_id)

    def clones(self) -> list[View]:
        """ :returns: All the other views into the same `Buffer`. See `View`. """
        return list(map(View, sublime_api.view_clones(self.view_id)))

    def file_name(self) -> Optional[str]:
        """
        :returns: The full name of the file associated with the sheet, or
                  ``None`` if it doesn't exist on disk.
        """
        name = sublime_api.view_file_name(self.view_id)
        if len(name) == 0:
            return None
        else:
            return name

    def close(self, on_close=lambda did_close: None) -> bool:
        """ Closes the view. """
        window_id = sublime_api.view_window(self.view_id)
        return sublime_api.window_close_file(window_id, self.view_id, on_close)

    def retarget(self, new_fname: str):
        """ Change the file path the buffer will save to. """
        sublime_api.view_retarget(self.view_id, new_fname)

    def name(self) -> str:
        """ :returns: The name assigned to the buffer, if any. """
        return sublime_api.view_get_name(self.view_id)

    def set_name(self, name: str):
        """
        Assign a name to the buffer. Displayed as in the tab for unsaved files.
        """
        sublime_api.view_set_name(self.view_id, name)

    def reset_reference_document(self):
        """
        Clears the state of the `incremental diff <incremental_diff>` for the
        view.
        """
        sublime_api.view_reset_reference_document(self.view_id)

    def set_reference_document(self, reference: str):
        """
        Uses the string reference to calculate the initial diff for the
        `incremental diff <incremental_diff>`.
        """
        sublime_api.view_set_reference_document(self.view_id, reference)

    def is_loading(self) -> bool:
        """
        :returns: Whether the buffer is still loading from disk, and not ready
                  for use.
        """
        return sublime_api.view_is_loading(self.view_id)

    def is_dirty(self) -> bool:
        """
        :returns: Whether there are any unsaved modifications to the buffer.
        """
        return sublime_api.view_is_dirty(self.view_id)

    def is_read_only(self) -> bool:
        """ :returns: Whether the buffer may not be modified. """
        return sublime_api.view_is_read_only(self.view_id)

    def set_read_only(self, read_only: bool):
        """ Set the read only property on the buffer. """
        return sublime_api.view_set_read_only(self.view_id, read_only)

    def is_scratch(self) -> bool:
        """
        :returns: Whether the buffer is a scratch buffer. See `set_scratch()`.
        """
        return sublime_api.view_is_scratch(self.view_id)

    def set_scratch(self, scratch: bool):
        """
        Sets the scratch property on the buffer. When a modified scratch buffer
        is closed, it will be closed without prompting to save. Scratch buffers
        never report as being dirty.
        """
        return sublime_api.view_set_scratch(self.view_id, scratch)

    def encoding(self) -> str:
        """
        :returns: The encoding currently associated with the buffer.
        """
        return sublime_api.view_encoding(self.view_id)

    def set_encoding(self, encoding_name: str):
        """
        Applies a new encoding to the file. This will be used when the file is
        saved.
        """
        sublime_api.view_set_encoding(self.view_id, encoding_name)

    def line_endings(self) -> str:
        """ :returns: The encoding currently associated with the file. """
        return sublime_api.view_line_endings(self.view_id)

    def set_line_endings(self, line_ending_name: str):
        """ Sets the line endings that will be applied when next saving. """
        sublime_api.view_set_line_endings(self.view_id, line_ending_name)

    def size(self) -> int:
        """ :returns: The number of character in the file. """
        return sublime_api.view_size(self.view_id)

    def begin_edit(self, edit_token: int, cmd: str, args: CommandArgs = None) -> Edit:
        sublime_api.view_begin_edit(self.view_id, edit_token, cmd, args)
        return Edit(edit_token)

    def end_edit(self, edit: Edit):
        sublime_api.view_end_edit(self.view_id, edit.edit_token)
        edit.edit_token = 0

    def is_in_edit(self) -> bool:
        return sublime_api.view_is_in_edit(self.view_id)

    def insert(self, edit: Edit, pt: Point, text: str) -> int:
        """
        Insert the given string into the buffer.

        :param edit: An `Edit` object provided by a `TextCommand`.
        :param point: The text point in the view where to insert.
        :param text: The text to insert.
        :returns: The actual number of characters inserted. This may differ
                  from the provided text due to tab translation.
        :raises ValueError: If the `Edit` object is in an invalid state, ie. outside of a `TextCommand`.
        """
        if edit.edit_token == 0:
            raise ValueError("Edit objects may not be used after the TextCommand's run method has returned")

        return sublime_api.view_insert(self.view_id, edit.edit_token, pt, text)

    def erase(self, edit: Edit, region: Region):
        """ Erases the contents of the provided `Region` from the buffer. """
        if edit.edit_token == 0:
            raise ValueError("Edit objects may not be used after the TextCommand's run method has returned")

        sublime_api.view_erase(self.view_id, edit.edit_token, region)

    def replace(self, edit: Edit, region: Region, text: str):
        """ Replaces the contents of the `Region` in the buffer with the provided string. """
        if edit.edit_token == 0:
            raise ValueError("Edit objects may not be used after the TextCommand's run method has returned")

        sublime_api.view_replace(self.view_id, edit.edit_token, region, text)

    def change_count(self) -> int:
        """
        Each time the buffer is modified, the change count is incremented. The
        change count can be used to determine if the buffer has changed since
        the last it was inspected.

        :returns: The current change count.
        """
        return sublime_api.view_change_count(self.view_id)

    def change_id(self) -> tuple[int, int, int]:
        """
        Get a 3-element tuple that can be passed to `transform_region_from()` to
        obtain a region equivalent to a region of the view in the past. This is
        primarily useful for plugins providing text modification that must
        operate in an asynchronous fashion and must be able to handle the view
        contents changing between the request and response.
        """
        return sublime_api.view_change_id(self.view_id)

    def transform_region_from(self, region: Region, change_id: tuple[int, int, int]) -> Region:
        """
        Transforms a region from a previous point in time to an equivalent
        region in the current state of the View. The ``change_id`` must have
        been obtained from `change_id()` at the point in time the region is
        from.
        """
        return sublime_api.view_transform_region_from(self.view_id, region, change_id)

    def run_command(self, cmd: str, args: CommandArgs = None):
        """ Run the named `TextCommand` with the (optional) given ``args``. """
        sublime_api.view_run_command(self.view_id, cmd, args)

    def sel(self) -> Selection:
        """ :returns: The views `Selection`. """
        return self.selection

    def substr(self, x: Region | Point) -> str:
        """
        :returns: The string at the `Point` or within the `Region` provided.
        """
        if isinstance(x, Region):
            return sublime_api.view_cached_substr(self.view_id, x.a, x.b)
        else:
            s = sublime_api.view_cached_substr(self.view_id, x, x + 1)
            # S2 backwards compat
            if len(s) == 0:
                return "\x00"
            else:
                return s

    def find(self, pattern: str, start_pt: Point, flags=FindFlags.NONE) -> Region:
        """
        :param pattern: The regex or literal pattern to search by.
        :param start_pt: The `Point` to start searching from.
        :param flags: Controls various behaviors of find. See `FindFlags`.
        :returns: The first `Region` matching the provided pattern.
        """
        return sublime_api.view_find(self.view_id, pattern, start_pt, flags)

    def find_all(self, pattern: str, flags=FindFlags.NONE, fmt: Optional[str] = None,
                 extractions: Optional[list[str]] = None) -> list[Region]:
        """
        :param pattern: The regex or literal pattern to search by.
        :param flags: Controls various behaviors of find. See `FindFlags`.
        :param fmt: When not ``None`` all matches in the ``extractions`` list
                       will be formatted with the provided format string.
        :param extractions: An optionally provided list to place the contents of
                            the find results into.
        :returns: All (non-overlapping) regions matching the pattern.
        """
        if fmt is None:
            return sublime_api.view_find_all(self.view_id, pattern, flags)
        else:
            results = sublime_api.view_find_all_with_contents(self.view_id, pattern, flags, fmt)
            ret = []
            for region, contents in results:
                ret.append(region)
                if extractions is not None:
                    extractions.append(contents)
            return ret

    def settings(self) -> Settings:
        """
        :returns: The view's `Settings` object. Any changes to it will be
                  private to this view.
        """
        if not self.settings_object:
            self.settings_object = Settings(sublime_api.view_settings(self.view_id))

        return self.settings_object

    def meta_info(self, key: str, pt: Point) -> Value:
        """
        Look up the preference ``key`` for the scope at the provided `Point`
        from all matching ``.tmPreferences`` files.

        Examples of keys are ``TM_COMMENT_START`` and ``showInSymbolList``.
        """
        return sublime_api.view_meta_info(self.view_id, key, pt)

    def extract_tokens_with_scopes(self, region: Region) -> list[tuple[Region, str]]:
        """
        :param region: The region from which to extract tokens and scopes.
        :returns: A list of pairs containing the `Region` and the scope of each token.

        .. since: 3172
        """
        return sublime_api.view_extract_tokens_with_scopes(self.view_id, region.begin(), region.end())

    def extract_scope(self, pt: Point) -> Region:
        """ :returns: The extent of the syntax scope name assigned to the character at the given `Point`, narrower syntax scope names included. """
        return sublime_api.view_extract_scope(self.view_id, pt)

    def expand_to_scope(self, pt: Point, selector: str) -> Optional[Region]:
        """
        Expand by the provided scope selector from the `Point`.

        :param pt: The point from which to expand.
        :param selector: The scope selector to match.
        :returns: The matched `Region`, if any.

        .. since: 4130
        """
        return sublime_api.view_expand_to_scope(self.view_id, pt, selector)

    def scope_name(self, pt: Point) -> str:
        """
        :returns: The syntax scope name assigned to the character at the given point.
        """
        return sublime_api.view_scope_name(self.view_id, pt)

    def context_backtrace(self, pt: Point) -> list[ContextStackFrame]:
        """ Get a backtrace of `ContextStackFrame`\\ s at the provided `Point`.

        Note this function is particularly slow.

        .. since:: 4127
        """
        return sublime_api.view_context_backtrace(self.view_id, pt)

    def match_selector(self, pt: Point, selector: str) -> bool:
        """
        :returns: Whether the provided scope selector matches the `Point`.
        """
        return sublime_api.view_match_selector(self.view_id, pt, selector)

    def score_selector(self, pt: Point, selector: str) -> int:
        """
        Equivalent to::

            sublime.score_selector(view.scope_name(pt), selector)

        See `sublime.score_selector`.
        """
        return sublime_api.view_score_selector(self.view_id, pt, selector)

    def find_by_selector(self, selector: str) -> list[Region]:
        """
        Find all regions in the file matching the given selector.

        :returns: The list of matched regions.
        """
        return sublime_api.view_find_by_selector(self.view_id, selector)

    def style(self) -> dict[str, str]:
        """
        See `style_for_scope`.

        :returns:
            The global style settings for the view. All colors are normalized
            to the six character hex form with a leading hash, e.g.
            ``#ff0000``.

        .. since:: 3150
        """
        return sublime_api.view_style(self.view_id)

    def style_for_scope(self, scope: str) -> dict[str, str]:
        """
        Accepts a string scope name and returns a ``dict`` of style information
        including the keys:

        * ``"foreground"``
        * ``"background"`` (only if set)
        * ``"bold"``
        * ``"italic"``
        * .. since:: 4063
            ``"glow"``
        * .. since:: 4075
            ``"underline"``
        * .. since:: 4075
            ``"stippled_underline"``
        * .. since:: 4075
            ``"squiggly_underline"``
        * ``"source_line"``
        * ``"source_column"``
        * ``"source_file"``

        The foreground and background colors are normalized to the six character
        hex form with a leading hash, e.g. ``#ff0000``.
        """
        return sublime_api.view_style_for_scope(self.view_id, scope)

    def indented_region(self, pt: Point) -> Region:
        return sublime_api.view_indented_region(self.view_id, pt)

    def indentation_level(self, pt: Point) -> int:
        return sublime_api.view_indentation_level(self.view_id, pt)

    def has_non_empty_selection_region(self) -> bool:
        return sublime_api.view_has_non_empty_selection_region(self.view_id)

    def lines(self, region: Region) -> list[Region]:
        """
        :returns: A list of lines (in sorted order) intersecting the provided `Region`.
        """
        return sublime_api.view_lines(self.view_id, region)

    def split_by_newlines(self, region: Region) -> list[Region]:
        """
        Splits the region up such that each `Region` returned exists on exactly
        one line.
        """
        return sublime_api.view_split_by_newlines(self.view_id, region)

    def line(self, x: Region | Point) -> Region:
        """
        :returns:
            The line that contains the `Point` or an expanded `Region` to the
            beginning/end of lines, excluding the newline character.
        """
        if isinstance(x, Region):
            return sublime_api.view_line_from_region(self.view_id, x)
        else:
            return sublime_api.view_line_from_point(self.view_id, x)

    def full_line(self, x: Region | Point) -> Region:
        """
        :returns:
            The line that contains the `Point` or an expanded `Region` to the
            beginning/end of lines, including the newline character.
        """
        if isinstance(x, Region):
            return sublime_api.view_full_line_from_region(self.view_id, x)
        else:
            return sublime_api.view_full_line_from_point(self.view_id, x)

    def word(self, x: Region | Point) -> Region:
        """
        :returns:
            The word that contains the provided `Point`. If a `Region` is
            provided it's beginning/end are expanded to word boundaries.
        """
        if isinstance(x, Region):
            return sublime_api.view_word_from_region(self.view_id, x)
        else:
            return sublime_api.view_word_from_point(self.view_id, x)

    def classify(self, pt: Point) -> PointClassification:
        """ Classify the provided `Point`. See `PointClassification`. """
        return PointClassification(sublime_api.view_classify(self.view_id, pt))

    def find_by_class(self, pt: Point, forward: bool, classes: PointClassification, separators="",
                      sub_word_separators="") -> Point:
        """
        Find the next location that matches the provided `PointClassification`.

        :param pt: The point to start searching from.
        :param forward: Whether to search forward or backwards.
        :param classes: The classification to search for.
        :param separators: The word separators to use when classifying.
        :param sub_word_separators:
            The sub-word separators to use when classifying. :since:`4130`
        :returns: The found point.
        """
        return sublime_api.view_find_by_class(self.view_id, pt, forward, classes, separators, sub_word_separators)

    def expand_by_class(self, x: Region | Point, classes: PointClassification, separators="",
                        sub_word_separators="") -> Region:
        """
        Expand the provided `Point` or `Region` to the left and right until each
        side lands on a location that matches the provided
        `PointClassification`. See `find_by_class`.

        :param classes: The classification to search by.
        :param separators: The word separators to use when classifying.
        :param sub_word_separators:
            The sub-word separators to use when classifying. :since:`4130`
        """
        if isinstance(x, Region):
            return sublime_api.view_expand_by_class(self.view_id, x.a, x.b, classes, separators, sub_word_separators)
        else:
            return sublime_api.view_expand_by_class(self.view_id, x, x, classes, separators, sub_word_separators)

    def rowcol(self, tp: Point) -> tuple[int, int]:
        """
        Calculates the 0-based line and column numbers of the point. Column
        numbers are returned as number of Unicode characters.
        """
        return sublime_api.view_row_col(self.view_id, tp)

    def rowcol_utf8(self, tp: Point) -> tuple[int, int]:
        """
        Calculates the 0-based line and column numbers of the point. Column
        numbers are returned as UTF-8 code units.

        .. since:: 4069
        """
        return sublime_api.view_row_col_utf8(self.view_id, tp)

    def rowcol_utf16(self, tp: Point) -> tuple[int, int]:
        """
        Calculates the 0-based line and column numbers of the point. Column
        numbers are returned as UTF-16 code units.

        .. since:: 4069
        """
        return sublime_api.view_row_col_utf16(self.view_id, tp)

    def text_point(self, row: int, col: int, *, clamp_column=False) -> Point:
        """
        Calculates the character offset of the given, 0-based, ``row`` and
        ``col``. ``col`` is interpreted as the number of Unicode characters to
        advance past the beginning of the row.

        :param clamp_column:
            Whether ``col`` should be restricted to valid values for the given
            ``row``. :since:`4075`
        """
        return sublime_api.view_text_point(self.view_id, row, col, clamp_column)

    def text_point_utf8(self, row: int, col: int, *, clamp_column=False) -> Point:
        """
        Calculates the character offset of the given, 0-based, ``row`` and
        ``col``. ``col`` is interpreted as the number of UTF-8 code units to
        advance past the beginning of the row.

        :param clamp_column:
            whether ``col`` should be restricted to valid values for the given
            ``row``. :since:`4075`
        """
        return sublime_api.view_text_point_utf8(self.view_id, row, col, clamp_column)

    def text_point_utf16(self, row: int, col: int, *, clamp_column=False) -> Point:
        """
        Calculates the character offset of the given, 0-based, ``row`` and
        ``col``. ``col`` is interpreted as the number of UTF-16 code units to
        advance past the beginning of the row.

        :param clamp_column:
            whether ``col`` should be restricted to valid values for the given
            ``row``. :since:`4075`
        """
        return sublime_api.view_text_point_utf16(self.view_id, row, col, clamp_column)

    def visible_region(self) -> Region:
        """ :returns: The currently visible area of the view. """
        return sublime_api.view_visible_region(self.view_id)

    def show(self, location: Region | Selection | Point, show_surrounds=True, keep_to_left=False, animate=True):
        """
        Scroll the view to show the given location.

        :param location:
            The location to scroll the view to. For a `Selection` only the first
            `Region` is shown.
        :param show_surrounds:
            Whether to show the surrounding context around the location.
        :param keep_to_left:
            Whether the view should be kept to the left, if horizontal scrolling
            is possible. :since:`4075`
        :param animate:
            Whether the scrolling should be animated. :since:`4075`
        """
        if isinstance(location, Region):
            sublime_api.view_show_region(self.view_id, location, show_surrounds, keep_to_left, animate)
        elif isinstance(location, Selection):
            for i in location:
                sublime_api.view_show_region(self.view_id, i, show_surrounds, keep_to_left, animate)
                return
        else:
            sublime_api.view_show_point(self.view_id, location, show_surrounds, keep_to_left, animate)

    def show_at_center(self, location: Region | Point, animate=True):
        """
        Scroll the view to center on the location.

        :param location: Which `Point` or `Region` to scroll to.
        :param animate: Whether the scrolling should be animated. :since:`4075`
        """
        if isinstance(location, Region):
            sublime_api.view_show_region_at_center(self.view_id, location, animate)
        else:
            sublime_api.view_show_point_at_center(self.view_id, location, animate)

    def viewport_position(self) -> Vector:
        """ :returns: The offset of the viewport in layout coordinates. """
        return sublime_api.view_viewport_position(self.view_id)

    def set_viewport_position(self, xy: Vector, animate=True):
        """ Scrolls the viewport to the given layout position. """
        sublime_api.view_set_viewport_position(self.view_id, xy, animate)

    def viewport_extent(self) -> Vector:
        """ :returns: The width and height of the viewport. """
        return sublime_api.view_viewport_extents(self.view_id)

    def layout_extent(self) -> Vector:
        """ :returns: The width and height of the layout. """
        return sublime_api.view_layout_extents(self.view_id)

    def text_to_layout(self, tp: Point) -> Vector:
        """ Convert a text point to a layout position. """
        return sublime_api.view_text_to_layout(self.view_id, tp)

    def text_to_window(self, tp: Point) -> Vector:
        """ Convert a text point to a window position. """
        return self.layout_to_window(self.text_to_layout(tp))

    def layout_to_text(self, xy: Vector) -> Point:
        """ Convert a layout position to a text point. """
        return sublime_api.view_layout_to_text(self.view_id, xy)

    def layout_to_window(self, xy: Vector) -> Vector:
        """ Convert a layout position to a window position. """
        return sublime_api.view_layout_to_window(self.view_id, xy)

    def window_to_layout(self, xy: Vector) -> Vector:
        """ Convert a window position to a layout position. """
        return sublime_api.view_window_to_layout(self.view_id, xy)

    def window_to_text(self, xy: Vector) -> Point:
        """ Convert a window position to a text point. """
        return self.layout_to_text(self.window_to_layout(xy))

    def line_height(self) -> DIP:
        """ :returns: The light height used in the layout. """
        return sublime_api.view_line_height(self.view_id)

    def em_width(self) -> DIP:
        """ :returns: The typical character width used in the layout. """
        return sublime_api.view_em_width(self.view_id)

    def is_folded(self, region: Region) -> bool:
        """ :returns: Whether the provided `Region` is folded. """
        return sublime_api.view_is_folded(self.view_id, region)

    def folded_regions(self) -> list[Region]:
        """ :returns: The list of folded regions. """
        return sublime_api.view_folded_regions(self.view_id)

    def fold(self, x: Region | list[Region]) -> bool:
        """
        Fold the provided `Region` (s).

        :returns: ``False`` if the regions were already folded.
        """
        if isinstance(x, Region):
            return sublime_api.view_fold_region(self.view_id, x)
        else:
            return sublime_api.view_fold_regions(self.view_id, x)

    def unfold(self, x: Region | list[Region]) -> list[Region]:
        """
        Unfold all text in the provided `Region` (s).

        :returns: The unfolded regions.
        """
        if isinstance(x, Region):
            return sublime_api.view_unfold_region(self.view_id, x)
        else:
            return sublime_api.view_unfold_regions(self.view_id, x)

    def add_regions(self, key: str, regions: list[Region], scope="",
                    icon="", flags=RegionFlags.NONE, annotations: list[str] = [],
                    annotation_color="",
                    on_navigate: Optional[Callable[[str], None]] = None,
                    on_close: Optional[Callable[[], None]] = None):
        """
        Adds visual indicators to regions of text in the view. Indicators
        include icons in the gutter, underlines under the text, borders around
        the text and annotations. Annotations are drawn aligned to the
        right-hand edge of the view and may contain HTML markup.

        :param key:
            An identifier for the collection of regions. If a set of regions
            already exists for this key they will be overridden. See
            `get_regions`.
        :param regions: The list of regions to add. These should not overlap.
        :param scope:
            An optional string used to source a color to draw the regions in.
            The scope is matched against the color scheme. Examples include:
            ``"invalid"`` and ``"string"``. See `Scope Naming <scope_naming>`
            for a list of common scopes. If the scope is empty, the regions
            won't be drawn.

            .. since:: 3148
                Also supports the following pseudo-scopes, to allow picking the
                closest color from the user‘s color scheme:

                * ``"region.redish"``
                * ``"region.orangish"``
                * ``"region.yellowish"``
                * ``"region.greenish"``
                * ``"region.cyanish"``
                * ``"region.bluish"``
                * ``"region.purplish"``
                * ``"region.pinkish"``
        :param icon:
            An optional string specifying an icon to draw in the gutter next to
            each region. The icon will be tinted using the color associated
            with the ``scope``. Standard icon names are ``"dot"``, ``"circle"`
            and ``"bookmark"``. The icon may also be a full package-relative
            path, such as ``"Packages/Theme - Default/dot.png"``.
        :param flags:
            Flags specifying how the region should be drawn, among other
            behavior. See `RegionFlags`.
        :param annotations:
            An optional collection of strings containing HTML documents to
            display along the right-hand edge of the view. There should be the
            same number of annotations as regions. See `minihtml` for supported
            HTML. :since:`4050`
        :param annotation_color:
            An optional string of the CSS color to use when drawing the left
            border of the annotation. See :ref:`minihtml Reference: Colors
            <minihtml:CSS:Colors>` for supported color formats. :since:`4050`
        :param on_navitate:
            Called when a link in an annotation is clicked. Will be passed the
            ``href`` of the link. :since:`4050`
        :param on_close:
            Called when the annotations are closed. :since:`4050`
        """

        # S2 has an add_regions overload that accepted flags as the 5th
        # positional argument, however this usage is no longer supported
        if not isinstance(icon, "".__class__):
            raise ValueError("icon must be a string")

        if not isinstance(annotations, list):
            raise ValueError("annotations must be a list")

        if len(annotations) != 0 and len(annotations) != len(regions):
            raise ValueError("region and annotation length mismatch")

        sublime_api.view_add_regions(
            self.view_id, key, regions, scope, icon, flags, annotations, annotation_color, on_navigate, on_close)

    def get_regions(self, key: str) -> list[Region]:
        """
        :returns: The regions associated with the given ``key``, if any.
        """
        return sublime_api.view_get_regions(self.view_id, key)

    def erase_regions(self, key: str):
        """
        Remove the regions associated with the given ``key``.
        """
        sublime_api.view_erase_regions(self.view_id, key)

    def add_phantom(self, key: str, region: Region, content: str, layout: PhantomLayout,
                    on_navigate: Optional[Callable[[str], None]] = None) -> int:
        return sublime_api.view_add_phantom(self.view_id, key, region, content, layout, on_navigate)

    def erase_phantoms(self, key: str):
        sublime_api.view_erase_phantoms(self.view_id, key)

    def erase_phantom_by_id(self, pid: int):
        sublime_api.view_erase_phantom(self.view_id, pid)

    def query_phantom(self, pid: int) -> list[Region]:
        return sublime_api.view_query_phantoms(self.view_id, [pid])

    def query_phantoms(self, pids: list[int]) -> list[Region]:
        return sublime_api.view_query_phantoms(self.view_id, pids)

    def assign_syntax(self, syntax: str | Syntax):
        """
        Changes the syntax used by the view. ``syntax`` may be a packages path
        to a syntax file, or a ``scope:`` specifier string.

        .. since:: 4080
            ``syntax`` may be a `Syntax` object.
        """
        if isinstance(syntax, Syntax):
            syntax = syntax.path

        sublime_api.view_assign_syntax(self.view_id, syntax)

    def set_syntax_file(self, syntax_file: str):
        """ :deprecated: Use `assign_syntax()` instead. """
        self.assign_syntax(syntax_file)

    def syntax(self) -> Optional[Syntax]:
        """ :returns: The syntax assigned to the buffer. """
        path = self.settings().get('syntax')
        if not path or not isinstance(path, str):
            return None
        return syntax_from_path(path)

    def symbols(self) -> list[tuple[Region, str]]:
        """
        Extract all the symbols defined in the buffer.

        :deprecated: Use `symbol_regions()` instead.
        """
        return sublime_api.view_symbols(self.view_id)

    def get_symbols(self) -> list[tuple[Region, str]]:
        """
        :deprecated: Use `symbol_regions()` instead.
        """
        return self.symbols()

    def indexed_symbols(self) -> list[tuple[Region, str]]:
        """
        :returns: A list of the `Region` and name of symbols.
        :deprecated: Use `indexed_symbol_regions()` instead.

        .. since:: 3148
        """
        return sublime_api.view_indexed_symbols(self.view_id)

    def indexed_references(self) -> list[tuple[Region, str]]:
        """
        :returns: A list of the `Region` and name of symbols.
        :deprecated: Use `indexed_symbol_regions()` instead.

        .. since:: 3148
        """
        return sublime_api.view_indexed_references(self.view_id)

    def symbol_regions(self) -> list[SymbolRegion]:
        """
        :returns: Info about symbols that are part of the view's symbol list.

        .. since:: 4085
        """
        return sublime_api.view_symbol_regions(self.view_id)

    def indexed_symbol_regions(self, type=SymbolType.ANY) -> list[SymbolRegion]:
        """
        :param type: The type of symbol to return.
        :returns: Info about symbols that are indexed.

        .. since:: 4085
        """
        return sublime_api.view_indexed_symbol_regions(self.view_id, type)

    def set_status(self, key: str, value: str):
        """
        Add the status ``key`` to the view. The ``value`` will be displayed in the
        status bar, in a comma separated list of all status values, ordered by
        key. Setting the ``value`` to ``""`` will clear the status.
        """
        sublime_api.view_set_status(self.view_id, key, value)

    def get_status(self, key: str) -> str:
        """
        :returns: The previous assigned value associated with the given ``key``, if any.

        See `set_status()`.
        """
        return sublime_api.view_get_status(self.view_id, key)

    def erase_status(self, key: str):
        """ Clear the status associated with the provided ``key``. """
        sublime_api.view_erase_status(self.view_id, key)

    def extract_completions(self, prefix: str, tp: Point = -1) -> list[str]:
        """
        Get a list of word-completions based on the contents of the view.

        :param prefix: The prefix to filter words by.
        :param tp: The `Point` by which to weigh words. Closer words are preferred.
        """
        return sublime_api.view_extract_completions(self.view_id, prefix, tp)

    def find_all_results(self) -> list[tuple[str, int, int]]:
        return sublime_api.view_find_all_results(self.view_id)

    def find_all_results_with_text(self) -> list[tuple[str, int, int, str]]:
        return sublime_api.view_find_all_results_with_text(self.view_id)

    def command_history(self, index: int, modifying_only=False) -> tuple[str, CommandArgs, int]:
        """
        Get info on previous run commands stored in the undo/redo stack.

        :param index:
            The offset into the undo/redo stack. Positive values for index
            indicate to look in the redo stack for commands.
        :param modifying_only:
            Whether only commands that modify the text buffer are considered.
        :returns:
            The command name, command arguments and repeat count for the history
            entry. If the undo/redo history doesn't extend far enough, then
            ``(None, None, 0)`` will be returned.
        """
        return sublime_api.view_command_history(self.view_id, index, modifying_only)

    def overwrite_status(self) -> bool:
        """
        :returns: The overwrite status, which the user normally toggles via the
                  insert key.
        """
        return sublime_api.view_get_overwrite_status(self.view_id)

    def set_overwrite_status(self, value: bool):
        """ Set the overwrite status. See `overwrite_status()`. """
        sublime_api.view_set_overwrite_status(self.view_id, value)

    def show_popup_menu(self, items: list[str], on_done: Callable[[int], None], flags=0):
        """
        Show a popup menu at the caret, for selecting an item in a list.

        :param items: The list of entries to show in the list.
        :param on_done: Called once with the index of the selected item. If the
                        popup was cancelled ``-1`` is passed instead.
        :param flags: must be ``0``, currently unused.
        """
        return sublime_api.view_show_popup_table(self.view_id, items, on_done, flags, -1)

    def show_popup(self, content: str, flags=PopupFlags.NONE, location: Point = -1,
                   max_width: DIP = 320, max_height: DIP = 240,
                   on_navigate: Optional[Callable[[str], None]] = None,
                   on_hide: Optional[Callable[[], None]] = None):
        """
        Show a popup displaying HTML content.

        :param content: The HTML content to display.
        :param flags: Flags controlling popup behavior. See `PopupFlags`.
        :param location: The `Point` at which to display the popup. If ``-1``
                         the popup is shown at the current postion of the caret.
        :param max_width: The maximum width of the popup.
        :param max_height: The maximum height of the popup.
        :param on_navigate:
            Called when a link is clicked in the popup. Passed the value of the
            ``href`` attribute of the clicked link.
        :param on_hide: Called when the popup is hidden.
        """
        sublime_api.view_show_popup(
            self.view_id, location, content, flags, max_width, max_height,
            on_navigate, on_hide)

    def update_popup(self, content: str):
        """
        Update the content of the currently visible popup.
        """
        sublime_api.view_update_popup_content(self.view_id, content)

    def is_popup_visible(self) -> bool:
        """
        :returns: Whether a popup is currently shown.
        """
        return sublime_api.view_is_popup_visible(self.view_id)

    def hide_popup(self):
        """
        Hide the current popup.
        """
        sublime_api.view_hide_popup(self.view_id)

    def is_auto_complete_visible(self) -> bool:
        """
        :returns: Whether the auto-complete menu is currently visible.
        """
        return sublime_api.view_is_auto_complete_visible(self.view_id)

    def preserve_auto_complete_on_focus_lost(self):
        """
        Sets the auto complete popup state to be preserved the next time the
        `View` loses focus. When the `View` regains focus, the auto complete
        window will be re-shown, with the previously selected entry
        pre-selected.

        .. since:: 4073
        """
        sublime_api.view_preserve_auto_complete_on_focus_lost(self.view_id)

    def export_to_html(self,
                       regions: Optional[Region | list[Region]] = None,
                       minihtml=False, enclosing_tags=False,
                       font_size=True, font_family=True):
        """
        Generates an HTML string of the current view contents, including styling
        for syntax highlighting.

        :param regions:
            The region(s) to export. By default the whole view is exported.
        :param minihtml:
            Whether the exported HTML should be compatible with `minihtml`.
        :param enclosing_tags:
            Whether a :html:`<div>` with base-styling is added. Note that
            without this no background color is set.
        :param font_size:
            Whether to include the font size in the top level styling. Only
            applies when ``enclosing_tags`` is ``True``.
        :param font_family:
            Whether to include the font family in the top level styling. Only
            applies when ``enclosing_tags`` is ``True``.

        .. since:: 4092
        """
        if regions is None:
            regions = [Region(0, self.size())]
        elif isinstance(regions, Region):
            regions = [regions]

        options = 0
        if enclosing_tags:
            options |= 1
        if minihtml:
            options |= 2
        if not font_size:
            options |= 4
        if not font_family:
            options |= 8

        return sublime_api.view_export_to_html(self.view_id, regions, options)

    def clear_undo_stack(self):
        """
        Clear the undo/redo stack.

        .. since:: 4114
        """
        sublime_api.view_clear_undo_stack(self.view_id)


def _buffers():
    return list(map(Buffer, sublime_api.buffers()))


class Buffer:
    """
    Represents a text buffer. Multiple `View` objects may share the same buffer.

    .. since:: 4081
    """

    def __init__(self, id):
        self.buffer_id = id

    def __hash__(self) -> int:
        return self.buffer_id

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Buffer) and self.buffer_id == other.buffer_id

    def __repr__(self) -> str:
        return f'Buffer({self.buffer_id!r})'

    def id(self) -> int:
        """
        Returns a number that uniquely identifies this buffer.

        .. since:: 4083
        """
        return self.buffer_id

    def file_name(self) -> Optional[str]:
        """
        The full name file the file associated with the buffer, or ``None`` if
        it doesn't exist on disk.

        .. since:: 4083
        """
        name = sublime_api.buffer_file_name(self.buffer_id)
        if len(name) == 0:
            return None
        else:
            return name

    def views(self) -> list[View]:
        """
        Returns a list of all views that are associated with this buffer.
        """
        return list(map(View, sublime_api.buffer_views(self.buffer_id)))

    def primary_view(self) -> View:
        """
        The primary view associated with this buffer.
        """
        return View(sublime_api.buffer_primary_view(self.buffer_id))


class Settings:
    """
    A ``dict`` like object that a settings hierarchy.
    """

    def __init__(self, id):
        self.settings_id = id

    def __getitem__(self, key: str) -> Value:
        """
        Returns the named setting.

        .. since:: 4023 3.8
        """
        res = sublime_api.settings_get(self.settings_id, key)
        if res is None and not sublime_api.settings_has(self.settings_id, key):
            raise KeyError(repr(key))
        return res

    def __setitem__(self, key: str, value: Value):
        """
        Set the named ``key`` to the provided ``value``.

        .. since:: 4023 3.8
        """
        sublime_api.settings_set(self.settings_id, key, value)

    def __delitem__(self, key: str):
        """
        Deletes the provided ``key`` from the setting. Note that a parent
        setting may also provide this key, thus deleting may not entirely
        remove a key.

        .. since:: 4078 3.8
        """
        sublime_api.settings_erase(self.settings_id, key)

    def __contains__(self, key: str) -> bool:
        """
        Returns whether the provided ``key`` is set.

        .. since:: 4023 3.8
        """
        return sublime_api.settings_has(self.settings_id, key)

    def __repr__(self) -> str:
        return f'Settings({self.settings_id!r})'

    def to_dict(self) -> dict:
        """
        Return the settings as a dict. This is not very fast.

        .. since:: 4078 3.8
        """
        return sublime_api.settings_to_dict(self.settings_id)

    def setdefault(self, key: str, value: Value):
        """
        Returns the value associated with the provided ``key``. If it's not
        present the provided ``value`` is assigned to the ``key`` and then
        returned.

        .. since:: 4023 3.8
        """
        if sublime_api.settings_has(self.settings_id, key):
            return sublime_api.settings_get(self.settings_id, key)
        sublime_api.settings_set(self.settings_id, key, value)
        return value

    def update(self, other=(), /, **kwargs):
        """
        Update the settings from the provided argument(s).

        Accepts:

        * A ``dict`` or other implementation of ``collections.abc.Mapping``.
        * An object with a ``keys()`` method.
        * An object that iterates over key/value pairs
        * Keyword arguments, ie. ``update(**kwargs)``.

        .. since:: 4078 3.8
        """
        if isinstance(other, collections.abc.Mapping):
            for key in other:
                self[key] = other[key]
        elif hasattr(other, 'keys'):
            for key in other.keys():
                self[key] = other[key]
        else:
            for key, value in other:
                self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def get(self, key: str, default: Value = None) -> Value:
        if default is not None:
            return sublime_api.settings_get_default(self.settings_id, key, default)
        else:
            return sublime_api.settings_get(self.settings_id, key)

    def has(self, key: str) -> bool:
        """ Same as `__contains__`. """
        return sublime_api.settings_has(self.settings_id, key)

    def set(self, key: str, value: Value):
        """ Same as `__setitem__`. """
        sublime_api.settings_set(self.settings_id, key, value)

    def erase(self, key: str):
        """ Same as `__delitem__`. """
        sublime_api.settings_erase(self.settings_id, key)

    def add_on_change(self, tag: str, callback: Callable[[], None]):
        """
        Register a callback to be run whenever a setting is changed.

        :param tag: A string associated with the callback. For use with
                    `clear_on_change`.
        :param callback: A callable object to be run when a setting is changed.
        """
        sublime_api.settings_add_on_change(self.settings_id, tag, callback)

    def clear_on_change(self, tag: str):
        """
        Remove all callbacks associated with the provided ``tag``. See
        `add_on_change`.
        """
        sublime_api.settings_clear_on_change(self.settings_id, tag)


class Phantom:
    """
    Represents an `minihtml`-based decoration to display non-editable content
    interspersed in a `View`. Used with `PhantomSet` to actually add the
    phantoms to the `View`. Once a `Phantom` has been constructed and added to
    the `View`, changes to the attributes will have no effect.
    """

    def __init__(self, region, content, layout, on_navigate=None):
        self.region: Region = region
        """
        The `Region` associated with the phantom. The phantom is displayed at
        the start of the `Region`.
        """
        self.content: str = content
        """ The HTML content of the phantom. """
        self.layout: PhantomLayout = layout
        """ How the phantom should be placed relative to the ``region``. """
        self.on_navigate: Optional[Callable[[str], None]] = on_navigate
        """
        Called when a link in the HTML is clicked. The value of the ``href``
        attribute is passed.
        """
        self.id = None

    def __eq__(self, rhs: object) -> bool:
        # Note that self.id is not considered
        return (isinstance(rhs, Phantom) and
                self.region == rhs.region and self.content == rhs.content and
                self.layout == rhs.layout and self.on_navigate == rhs.on_navigate)

    def __repr__(self) -> str:
        return (f'Phantom({self.region!r}, {self.content!r}, '
                f'{self.layout!r}, on_navigate={self.on_navigate!r})')

    def to_tuple(self) -> tuple[tuple[Point, Point], str, PhantomLayout, Optional[Callable[[str], None]]]:
        """
        Returns a tuple of this phantom containing the region, content, layout
        and callback.

        Use this to uniquely identify a phantom in a set or similar. Phantoms
        can't be used for that directly as they are mutable.
        """
        return (self.region.to_tuple(), self.content, self.layout, self.on_navigate)


class PhantomSet:
    """
    A collection that manages `Phantom` objects and the process of adding them,
    updating them and removing them from a `View`.
    """

    def __init__(self, view, key=""):
        """
        """
        self.view: View = view
        """
        The `View` the phantom set is attached to.
        """
        self.key: str = key
        """
        A string used to group the phantoms together.
        """
        self.phantoms: [Phantom] = []

    def __del__(self):
        for p in self.phantoms:
            self.view.erase_phantom_by_id(p.id)

    def __repr__(self) -> str:
        return f'PhantomSet({self.view!r}, key={self.key!r})'

    def update(self, phantoms: Iterator[Phantom]):
        """
        Update the set of phantoms. If the `Phantom.region` of existing phantoms
        have changed they will be moved; new phantoms are added and ones not
        present are removed.
        """
        new_phantoms = {p.to_tuple(): p for p in phantoms}

        # Update the list of phantoms that exist in the text buffer with their
        # current location
        regions = self.view.query_phantoms([p.id for p in self.phantoms])
        for phantom, region in zip(self.phantoms, regions):
            phantom.region = region

        current_phantoms = {p.to_tuple(): p for p in self.phantoms}

        for key, p in new_phantoms.items():
            try:
                # Phantom already exists, copy the id from the current one
                p.id = current_phantoms[key].id
            except KeyError:
                p.id = self.view.add_phantom(
                    self.key, p.region, p.content, p.layout, p.on_navigate)

        new_phantom_ids = set([p.id for p in new_phantoms.values()])

        for p in self.phantoms:
            # if the region is -1, then it's already been deleted, no need to
            # call erase
            if p.id not in new_phantom_ids and p.region != Region(-1):
                self.view.erase_phantom_by_id(p.id)

        self.phantoms = [p for p in new_phantoms.values()]


class Html:
    """
    Used to indicate that a string is formatted as HTML. See
    `CommandInputHandler.preview()`.
    """

    __slots__ = ['data']

    def __init__(self, data):
        self.data: str = data

    def __repr__(self) -> str:
        return f'Html({self.data})'


class CompletionList:
    """
    Represents a list of completions, some of which may be in the process of
    being asynchronously fetched.

    .. since:: 4050
    """

    def __init__(self, completions: Optional[list[CompletionValue]] = None, flags=AutoCompleteFlags.NONE):
        """
        :param completions:
            If ``None`` is passed, the method `set_completions()` must be called
            before the completions will be displayed to the user.
        :param flags: Flags controlling auto-complete behavior. See `AutoCompleteFlags`.
        """
        self.target = None
        self.completions = completions
        self.flags = flags

    def __repr__(self) -> str:
        return f'CompletionList(completions={self.completions!r}, flags={self.flags!r})'

    def _set_target(self, target):
        if self.completions is not None:
            target.completions_ready(self.completions, self.flags)
        else:
            self.target = target

    def set_completions(self, completions: list[CompletionValue], flags=AutoCompleteFlags.NONE):
        """
        Sets the list of completions, allowing the list to be displayed to the
        user.
        """
        assert(self.completions is None)
        assert(flags is not None)

        self.completions = completions
        self.flags = flags

        if self.target is not None:
            self.target.completions_ready(completions, flags)


class CompletionItem:
    """
    Represents an available auto-completion item.

    .. since:: 4050
    """

    __slots__ = [
        'trigger',
        'annotation',
        'completion',
        'completion_format',
        'kind',
        'details',
        'flags'
    ]

    def __init__(
            self,
            trigger,
            annotation="",
            completion="",
            completion_format=CompletionFormat.TEXT,
            kind=KIND_AMBIGUOUS,
            details="",
            flags=CompletionItemFlags.NONE):

        self.trigger: str = trigger
        """ Text to match against the user's input. """
        self.annotation: str = annotation
        """ A hint to draw to the right-hand side of the trigger. """
        self.completion: str = completion
        """
        Text to insert if the completion is specified. If empty the `trigger`
        will be inserted instead.
        """
        self.completion_format: CompletionFormat = completion_format
        """ The format of the completion. See `CompletionFormat`. """
        self.kind: Kind = kind
        """ The kind of the completion. See `Kind`. """
        self.details: str = details
        """
        An optional `minihtml` description of the completion, shown in the
        detail pane at the bottom of the auto complete window.

        .. since:: 4073
        """
        self.flags = flags

    def __eq__(self, rhs: object) -> bool:
        if not isinstance(rhs, CompletionItem):
            return False
        if self.trigger != rhs.trigger:
            return False
        if self.annotation != rhs.annotation:
            return False
        if self.completion != rhs.completion:
            return False
        if self.completion_format != rhs.completion_format:
            return False
        if tuple(self.kind) != tuple(rhs.kind):
            return False
        if self.details != rhs.details:
            return False
        if self.flags != rhs.flags:
            return False
        return True

    def __repr__(self) -> str:
        return (f'CompletionItem({self.trigger!r}, '
                f'annotation={self.annotation!r}, '
                f'completion={self.completion!r}, '
                f'completion_format={self.completion_format!r}, '
                f'kind={self.kind!r}, details={self.details!r}, '
                f'flags={self.flags!r})')

    @classmethod
    def snippet_completion(
            cls,
            trigger: str,
            snippet: str,
            annotation="",
            kind=KIND_SNIPPET,
            details="") -> 'CompletionItem':
        """
        Specialized constructor for snippet completions. The `completion_format`
        is always `CompletionFormat.SNIPPET`.
        """
        return CompletionItem(
            trigger,
            annotation,
            snippet,
            COMPLETION_FORMAT_SNIPPET,
            kind,
            details)

    @classmethod
    def command_completion(
            cls,
            trigger: str,
            command: str,
            args: CommandArgs = None,
            annotation="",
            kind=KIND_AMBIGUOUS,
            details="") -> 'CompletionItem':
        """
        Specialized constructor for command completions. The `completion_format`
        is always `CompletionFormat.COMMAND`.
        """
        return CompletionItem(
            trigger,
            annotation,
            format_command(command, args),
            COMPLETION_FORMAT_COMMAND,
            kind,
            details)


def list_syntaxes() -> list[Syntax]:
    """ list all known syntaxes.

    Returns a list of Syntax.
    """
    return sublime_api.list_syntaxes()


def syntax_from_path(path: str) -> Optional[Syntax]:
    """ Get the syntax for a specific path.

    Returns a Syntax or None.
    """
    return sublime_api.get_syntax(path)


def find_syntax_by_name(name: str) -> list[Syntax]:
    """ Find syntaxes with the specified name.

    Name must match exactly. Return a list of Syntax.
    """
    return [syntax for syntax in list_syntaxes() if syntax.name == name]


def find_syntax_by_scope(scope: str) -> list[Syntax]:
    """ Find syntaxes with the specified scope.

    Scope must match exactly. Return a list of Syntax.
    """
    return [syntax for syntax in list_syntaxes() if syntax.scope == scope]


def find_syntax_for_file(path, first_line="") -> Optional[Syntax]:
    """ Find the syntax to use for a path.

    Uses the file extension, various application settings and optionally the
    first line of the file to pick the right syntax for the file.

    Returns a Syntax.
    """
    if not isinstance(first_line, str):
        raise TypeError('a str is required for first_line')

    if len(first_line) > 1024:
        first_line = first_line[:1024]

    return sublime_api.find_syntax_for_file(path, first_line)


class Syntax:
    """
    Contains information about a syntax.

    .. since:: 4081
    """

    __slots__ = ['path', 'name', 'hidden', 'scope']

    def __init__(self, path, name, hidden, scope):
        self.path: str = path
        """ The packages path to the syntax file. """
        self.name: str = name
        """ The name of the syntax. """
        self.hidden: bool = hidden
        """ If the syntax is hidden from the user. """
        self.scope: str = scope
        """ The base scope name of the syntax. """

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Syntax) and self.path == other.path

    def __hash__(self) -> int:
        return hash(self.path)

    def __repr__(self) -> str:
        return (f'Syntax({self.path!r}, {self.name!r}, {self.hidden!r}, '
                f'{self.scope!r})')


class QuickPanelItem:
    """
    Represents a row in the quick panel, shown via `Window.show_quick_panel()`.

    .. since:: 4083
    """

    __slots__ = ['trigger', 'details', 'annotation', 'kind']

    def __init__(self, trigger, details="", annotation="", kind=KIND_AMBIGUOUS):
        self.trigger: str = trigger
        """ Text to match against user's input. """
        self.details: str | list[str] | tuple[str] = details
        """
        A `minihtml` string or list of strings displayed below the trigger.
        """
        self.annotation: str = annotation
        """ Hint to draw to the right-hand side of the row. """
        self.kind: Kind = kind
        """ The kind of the item. See `Kind`. """

    def __repr__(self) -> str:
        return (f'QuickPanelItem({self.trigger!r}, '
                f'details={self.details!r}, '
                f'annotation={self.annotation!r}, '
                f'kind={self.kind!r})')


class ListInputItem:
    """
    Represents a row shown via `ListInputHandler`.

    .. since:: 4095
    """

    __slots__ = ['text', 'value', 'details', 'annotation', 'kind']

    def __init__(self, text, value, details="", annotation="", kind=KIND_AMBIGUOUS):
        self.text: str = text
        """ Text to match against the user's input. """
        self.value: Any = value
        """ A `Value` passed to the command if the row is selected. """
        self.details: str | list[str] | tuple[str] = details
        """
        A `minihtml` string or list of strings displayed below the trigger.
        """
        self.annotation: str = annotation
        """ Hint to draw to the right-hand side of the row. """
        self.kind: Kind = kind
        """ The kind of the item. See `Kind`. """

    def __repr__(self) -> str:
        return (f'ListInputItem({self.text!r}, '
                f'value={self.value!r}, '
                f'details={self.details!r}, '
                f'annotation={self.annotation!r}, '
                f'kind={self.kind!r})')


class SymbolRegion:
    """
    Contains information about a `Region` of a `View` that contains a symbol.

    .. since:: 4085
    """

    __slots__ = ['name', 'region', 'syntax', 'type', 'kind']

    def __init__(self, name, region, syntax, type, kind):
        self.name: str = name
        """ The name of the symbol. """
        self.region: Region = region
        """ The location of the symbol within the `View`. """
        self.syntax: str = syntax
        """ The name of the syntax for the symbol. """
        self.type: SymbolType = type
        """ The type of the symbol. See `SymbolType`. """
        self.kind: Kind = kind
        """ The kind of the symbol. See `Kind`. """

    def __repr__(self) -> str:
        return (f'SymbolRegion({self.name!r}, {self.region!r}, '
                f'syntax={self.syntax!r}, type={self.type!r}, '
                f'kind={self.kind!r})')


class SymbolLocation:
    """
    Contains information about a file that contains a symbol.

    .. since:: 4085
    """

    __slots__ = ['path', 'display_name', 'row', 'col', 'syntax', 'type', 'kind']

    def __init__(self, path, display_name, row, col, syntax, type, kind):
        self.path: str = path
        """ The filesystem path to the file containing the symbol. """
        self.display_name: str = display_name
        """ The project-relative path to the file containing the symbol. """
        self.row: int = row
        """ The row of the file the symbol is contained on. """
        self.col: int = col
        """ The column of the row that the symbol is contained on. """
        self.syntax: str = syntax
        """ The name of the syntax for the symbol. """
        self.type: SymbolType = type
        """ The type of the symbol. See `SymbolType`. """
        self.kind: Kind = kind
        """ The kind of the symbol. See `Kind`. """

    def __repr__(self) -> str:
        return (f'SymbolLocation({self.path!r}, {self.display_name!r}, '
                f'row={self.row!r}, col={self.col!r}, syntax={self.syntax!r}, '
                f'type={self.type!r}, kind={self.kind!r})')

    def path_encoded_position(self) -> str:
        return "%s:%d:%d" % (self.path, self.row, self.col)
