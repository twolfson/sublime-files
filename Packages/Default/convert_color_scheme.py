import json
import plistlib
import re
from collections import OrderedDict

import sublime
import sublime_plugin

from .colors import (
    BASE_RED,
    BASE_ORANGE,
    BASE_YELLOW,
    BASE_GREEN,
    BASE_BLUE,
    BASE_PURPLE,
    BASE_PINK,
    X11_COLORS,
    color_diff,
    HSLA,
)


class ColorCatalog():
    """
    Catalog of colors used in a color scheme
    """

    store = None
    names = None
    name_map = None

    def __init__(self):
        self.store = {}

    def items(self):
        """
        :return:
            A list of tuples containing (string name, HSLA color)
        """

        self._generate_maps()
        return self.names.items()

    def name(self, hsla):
        """
        :param hsla:
            An HSLA object

        :return:
            A string name for the color
        """

        self._generate_maps()
        return self.name_map[hsla]

    def _generate_maps(self):
        """
        Generates names for each color based on diff from base colors
        """

        if self.names is None:
            self.names = OrderedDict()
            self.name_map = {}
            for base in sorted(self.store.keys()):
                for i, info in enumerate(sorted(self.store[base].keys())):
                    suffix = '' if i == 0 else str(i + 1)
                    hsla = self.store[base][info]
                    self.names[base + suffix] = hsla
                    self.name_map[hsla] = base + suffix

    def lookup(self, hsla):
        """
        :param hsla:
            An HSLA object

        :return:
            A CSSColor object for the HSLA object
        """

        base, diff = self.base_diff(hsla)

        if base not in self.store:
            self.store[base] = {}

        index = -1 * hsla.l if hsla.l > 0.5 else hsla.l
        if (diff, index) not in self.store[base]:
            self.names = None
            self.name_map = None
            self.store[base][(diff, index)] = hsla.full_alpha()

        return CSSColor(self, base, diff, hsla)

    @classmethod
    def base_diff(cls, hsla):
        """
        :param hsla:
            An HSLA object

        :return:
            A 2-element tuple of (string base color, float diff)
        """

        if hsla.l < 0.15:
            return ('black', color_diff(hsla, HSLA(0.0, 0.0, 0.0, 1.0)))

        if hsla.l > 0.85:
            return ('white', color_diff(hsla, HSLA(1.0, 1.0, 1.0, 1.0)))

        if hsla.s < 0.1:
            return ('grey', color_diff(hsla, HSLA(0.5, 0.5, 0.5, 1.0)))

        comparisons = [
            ('red', BASE_RED),
            ('orange', BASE_ORANGE),
            ('yellow', BASE_YELLOW),
            ('green', BASE_GREEN),
            ('blue', BASE_BLUE),
            ('purple', BASE_PURPLE),
            ('pink', BASE_PINK),
        ]

        diff = 128.0
        for bname, bc in comparisons:
            bdiff = color_diff(bc, hsla)
            if bdiff < diff:
                diff = bdiff
                base = bname

        return (base, diff)


class CSSColor():
    """
    A representation of an HSLA color for use in a CSS document
    """

    catalog = None
    base = None
    diff = None
    color = None

    def __init__(self, catalog, base, diff, color):
        self.catalog = catalog
        self.base = base
        self.diff = diff
        self.color = color

    def dump(self):
        """
        :return:
            A string of the color for use in a CSS document
        """

        name = self.catalog.name(self.color.full_alpha())
        if self.color.a < 1.0:
            return 'color(var(%s) alpha(%.2g))' % (name, self.color.a)
        return 'var(%s)' % name


class HexCSSColorEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CSSColor):
            return obj.dump()
        if isinstance(obj, HSLA):
            return obj.to_hex()
        return json.JSONEncoder.default(self, obj)


class HSLCSSColorEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, CSSColor):
            return obj.dump()
        if isinstance(obj, HSLA):
            hue = int(obj.h * 360.0 + 0.5)
            sat = int(obj.s * 100.0 + 0.5)
            lum = int(obj.l * 100.0 + 0.5)
            return 'hsl(%d, %d%%, %d%%)' % (hue, sat, lum)
        return json.JSONEncoder.default(self, obj)


class UseVariablesInputHandler(sublime_plugin.ListInputHandler):
    options = {
        'hsl': 'HSL - use HSL variables for colors',
        'yes': 'Hex - use hex variables for colors',
        'no': 'None - hardcode all colors'
    }

    def placeholder(self):
        return 'Use variables'

    def list_items(self):
        return [self.options['hsl'], self.options['yes'], self.options['no']]


class ConvertColorSchemeCommand(sublime_plugin.WindowCommand):
    global_settings = OrderedDict([
        ('foreground', 'foreground'),
        ('background', 'background'),
        ('accent', 'accent'),
        ('caret', 'caret'),
        ('invisibles', 'invisibles'),
        ('lineHighlight', 'line_highlight'),
        ('rulers', 'rulers'),
        ('selection', 'selection'),

        ('selectionForeground', 'selection_foreground'),
        ('selectionBorder', 'selection_border'),
        ('inactiveSelection', 'inactive_selection'),
        ('inactiveSelectionForeground', 'inactive_selection_foreground'),
        ('misspelling', 'misspelling'),
        ('minimapBorder', 'minimap_border'),
        ('gutter', 'gutter'),
        ('gutterForeground', 'gutter_foreground'),
        ('shadow', 'shadow'),
        ('shadowWidth', 'shadow_width'),
        ('guide', 'guide'),
        ('activeGuide', 'active_guide'),
        ('stackGuide', 'stack_guide'),
        ('highlight', 'highlight'),
        ('findHighlightForeground', 'find_highlight_foreground'),
        ('findHighlight', 'find_highlight'),
        ('bracketsOptions', 'brackets_options'),
        ('bracketsForeground', 'brackets_foreground'),
        ('bracketContentsOptions', 'bracket_contents_options'),
        ('bracketContentsForeground', 'bracket_contents_foreground'),
        ('tagsOptions', 'tags_options'),
        ('tagsForeground', 'tags_foreground'),
        ('popupCss', 'popup_css'),
        ('phantomCss', 'phantom_css'),
    ])

    non_color_settings = [
        'shadow_width',
        'brackets_options',
        'bracket_contents_options',
        'tags_options',
        'popup_css',
        'phantom_css',
    ]

    def run(self, use_variables=None):
        use_vars = use_variables != UseVariablesInputHandler.options['no']
        hsl_vars = use_variables == UseVariablesInputHandler.options['hsl']

        view = self.window.active_view()
        if not view:
            return
        fname = view.file_name()
        if not fname or not fname.endswith('.tmTheme'):
            return
        tm_theme = view.substr(sublime.Region(0, view.size()))
        plist = plistlib.readPlistFromBytes(tm_theme.encode("utf-8"))

        scheme = OrderedDict()
        scheme["name"] = plist.get("name", "Unnamed")
        scheme["author"] = plist.get("author", "Unknown")

        globals = OrderedDict()
        rules = []
        colors = ColorCatalog()

        for setting in plist.get("settings", []):
            if "scope" in setting:
                rule = OrderedDict()
                if "name" in setting:
                    rule["name"] = setting["name"]
                if "scope" in setting:
                    rule["scope"] = setting["scope"]
                if "settings" in setting:
                    details = setting["settings"]
                    if "foreground" in details:
                        rule["foreground"] = self.resolve(use_vars, colors, details["foreground"])
                    if "selectionForeground" in details:
                        rule["selection_foreground"] = self.resolve(use_vars, colors, details["selectionForeground"])
                    if "background" in details:
                        rule["background"] = self.resolve(use_vars, colors, details["background"])
                    if "fontStyle" in details and details["fontStyle"].strip() != "":
                        rule["font_style"] = details["fontStyle"].strip()
                rules.append(rule)

            else:
                details = setting.get('settings', {})
                for tm_key in self.global_settings:
                    if tm_key not in details:
                        continue
                    value = details[tm_key]
                    subl_key = self.global_settings[tm_key]
                    if subl_key not in self.non_color_settings:
                        value = self.resolve(use_vars, colors, value)
                    if subl_key.endswith('_options'):
                        value = value.strip()
                    globals[subl_key] = value

        if use_vars:
            variables = OrderedDict()
            for name, color in colors.items():
                variables[name] = color
            if len(variables) > 0:
                scheme["variables"] = variables

        scheme["globals"] = globals
        scheme["rules"] = rules

        if hsl_vars:
            encoder_cls = HSLCSSColorEncoder
        else:
            encoder_cls = HexCSSColorEncoder
        sublime_color_scheme = json.dumps(scheme, indent=4, cls=encoder_cls)

        # Trim trailing whitespace
        sublime_color_scheme = re.sub(r'\s+$', '', sublime_color_scheme, 0, re.M)
        # Put [ and { on the next line
        sublime_color_scheme = re.sub(r'^(\s+)("\w+":) ([\[{])\n', '\\1\\2\n\\1\\3\n', sublime_color_scheme, 0, re.M)

        new_view = self.window.new_file()
        self.window.focus_view(new_view)
        new_view.settings().set('syntax', 'Packages/JavaScript/JSON.sublime-syntax')
        new_view.run_command('append', {'characters': sublime_color_scheme})
        new_view.set_viewport_position((0, 0))
        new_view.set_name(scheme['name'] + '.sublime-color-scheme')

    def resolve(self, use_vars, colors, value):
        """
        Returns a CSS value for the color specified

        :param use_vars:
            If the .sublime-color-scheme variables functionality should be used

        :param colors:
            A dict mapping string CSS color to string variable name

        :param value:
            A string CSS color

        :return:
            A string containing a CSS color, variable or function
        """

        if not use_vars:
            return value

        if value in X11_COLORS:
            value = X11_COLORS[value]

        return colors.lookup(HSLA.from_hex(value))

    def input(self, args):
        if 'use_variables' not in args:
            return UseVariablesInputHandler()
        return None

    def is_enabled(self):
        view = self.window.active_view()
        if not view:
            return False
        fname = view.file_name()
        return fname is not None and fname.endswith('.tmTheme')
