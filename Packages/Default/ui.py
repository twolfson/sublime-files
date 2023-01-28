import sublime
import sublime_plugin

import os


PREFS_FILE = 'Preferences.sublime-settings'
DEFAULT_CS = 'Mariana.sublime-color-scheme'
DEFAULT_THEME = 'Default.sublime-theme'

CURRENT_KIND = (sublime.KIND_ID_COLOR_GREENISH, "✓", "Current")


class SelectColorSchemeCommand(sublime_plugin.WindowCommand):
    def run(self, name, light=None, dark=None):
        settings = sublime.load_settings(PREFS_FILE)
        settings.set('color_scheme', name)
        if light:
            settings.set('light_color_scheme', light)
        if dark:
            settings.set('dark_color_scheme', dark)
        sublime.save_settings(PREFS_FILE)

    def input(self, args):
        if "name" not in args:
            return ColorSchemeInputHandler(
                "Name",
                "name",
                False,
                "color_scheme",
                DEFAULT_CS,
                ""
            )
        else:
            return None


class ColorSchemeInputHandler(sublime_plugin.ListInputHandler):
    # The current window
    window = None

    # A list of info about active views in the current window that have
    # view-specific color scheme. This ensures the preview process is at
    # least previewing the color scheme for things the user can see.
    views = None

    # A sublime.Settings object of the global Sublime Text settings
    prefs = None

    # The color_scheme when this input handler was created
    original = None

    # The last previewed color_scheme - used to debounce the search so we
    # aren't applying a new color scheme with every keypress
    last_previewed = None

    # The placeholder to show in the command palette
    placeholder_ = None

    # The name of the arg to fill in
    arg_name = None

    # If the user is selecting the light or dark variant
    variant = False

    # The name of the setting to load the previous value for
    setting_name = None

    # The default value if the setting is missing
    default_value = None

    # The value to pre-select
    pre_selection = None

    # A string prefix to place before the selected value
    prefix = None

    def __init__(self, placeholder, arg_name, variant, setting_name, default_value, prefix):
        self.placeholder_ = placeholder
        self.arg_name = arg_name
        self.variant = variant
        self.setting_name = setting_name
        self.default_value = default_value
        self.prefix = prefix

    def name(self):
        return self.arg_name

    def placeholder(self):
        return self.placeholder_

    def cancel(self):
        self.reset_views()
        self.prefs.set('color_scheme', self.original)
        sublime.save_settings(PREFS_FILE)

    def confirm(self, name):
        self.reset_views()

    def description(self, v, text):
        if self.prefix:
            return self.prefix + text
        return text

    def next_input(self, args):
        if "name" in args and args["name"] == "auto":
            if "light" not in args:
                return ColorSchemeInputHandler(
                    "Light variant",
                    "light",
                    True,
                    "light_color_scheme",
                    "Breakers.sublime-color-scheme",
                    "Light: "
                )
            elif "dark" not in args:
                return ColorSchemeInputHandler(
                    "Dark variant",
                    "dark",
                    True,
                    "dark_color_scheme",
                    "Mariana.sublime-color-scheme",
                    "Dark: "
                )
        else:
            None

    def preview(self, name):
        if name is None:
            return

        self.last_previewed = name

        def update_cs():
            # The color scheme to preview has been updated since
            # the timeout was created
            if name != self.last_previewed:
                return
            if self.prefs.get('color_scheme') == name:
                return
            self.prefs.set('color_scheme', name)
            for i in self.overridden_views():
                i['settings'].set('color_scheme', name)
        sublime.set_timeout(update_cs, 250)

        return None

    def list_items(self):
        self.window = sublime.active_window()
        self.prefs = sublime.load_settings(PREFS_FILE)

        self.original = self.prefs.get('color_scheme', DEFAULT_CS)
        self.pre_selection = self.prefs.get(self.setting_name, self.default_value)

        # sublime-color-scheme's are unique on the name, but tmTheme's are
        # unique on the path
        if self.original.endswith(".sublime-color-scheme"):
            self.original = os.path.basename(self.original)
        if self.pre_selection.endswith(".sublime-color-scheme"):
            self.pre_selection = os.path.basename(self.pre_selection)

        show_legacy = self.prefs.get("show_legacy_color_schemes", False)

        items = []
        selected = -1

        if not self.variant:
            kind_info = sublime.KIND_AMBIGUOUS
            if self.pre_selection == "auto":
                kind_info = CURRENT_KIND
                selected = 0

            items.append(sublime.ListInputItem(
                'Auto',
                'auto',
                details='Switches between light and dark color schemes to match OS appearance',
                kind=kind_info
            ))

        files = []
        nameset = set()
        for f in sublime.find_resources('*.tmTheme'):
            files.append((f, f))
            nameset.add(os.path.splitext(os.path.basename(f))[0])

        # Color schemes with the same name are merged, but that's not the case
        # for tmTheme.
        for f in sublime.find_resources('*.sublime-color-scheme'):
            basename = os.path.basename(f)
            name = os.path.splitext(basename)[0]
            if name not in nameset:
                nameset.add(name)
                files.append((f, basename))

        for cs, unique_path in files:
            pkg, basename = os.path.split(cs)
            name = os.path.splitext(basename)[0]

            if pkg == "Packages/Color Scheme - Legacy" and not show_legacy:
                continue

            kind_info = sublime.KIND_AMBIGUOUS
            if self.pre_selection and self.pre_selection == unique_path:
                kind_info = CURRENT_KIND
                selected = len(items)

            if pkg.startswith("Packages/"):
                pkg = pkg[len("Packages/"):]

            items.append(sublime.ListInputItem(name, unique_path, details=pkg, kind=kind_info))

        return (items, selected)

    def overridden_views(self, find=True):
        """
        :param find:
            A bool that controls if the list of views with overridden
            color scheme should be determined, if not already present

        :return:
            A list of dict objects containing the keys:
             - "settings": a sublime.Settings object for the view
             - "original": a string of the original "color_scheme" setting for the view
        """

        if self.views is None:
            if find is False:
                return []
            # If the color scheme hasn't been changed, we won't
            # be able to detect overrides
            if self.prefs.get('color_scheme') == self.original:
                return []
            vs = []
            for i in range(self.window.num_groups()):
                v = self.window.active_view_in_group(i)
                if v:
                    cs = v.settings().get('color_scheme', DEFAULT_CS)
                    if self.is_view_specific(v):
                        vs.append({
                            'settings': v.settings(),
                            'original': cs,
                        })
            self.views = vs
        return self.views

    def is_view_specific(self, view):
        """
        :param view:
            A sublime.View object

        :return:
            A bool if the color_scheme is specific to the view
        """

        vcs = view.settings().get('color_scheme', DEFAULT_CS)
        pd = self.window.project_data()
        pcs = None
        if pd is not None:
            pcs = pd.get('settings', {}).get('color_scheme')
        gcs = self.prefs.get('color_scheme')

        if pcs is not None and vcs != pcs:
            return True
        return vcs != gcs

    def reset_views(self):
        """
        Reset view-specific color schemes
        """

        for i in self.overridden_views(find=False):
            i['settings'].set('color_scheme', i['original'])


class SelectThemeCommand(sublime_plugin.WindowCommand):
    def run(self, name, light=None, dark=None):
        settings = sublime.load_settings(PREFS_FILE)
        settings.set('theme', name)
        if light:
            settings.set('light_theme', light)
        if dark:
            settings.set('dark_theme', dark)
        sublime.save_settings(PREFS_FILE)

    def input(self, args):
        if "name" not in args:
            return ThemeInputHandler(
                "Name",
                "name",
                False,
                "theme",
                DEFAULT_THEME,
                ""
            )
        else:
            return None


class ThemeInputHandler(sublime_plugin.ListInputHandler):
    # The current window
    window = None

    # A sublime.Settings object of the global Sublime Text settings
    prefs = None

    # The theme when this input handler was created
    original = None

    # The last previewed theme - used to debounce the search so we
    # aren't applying a new color scheme with every keypress
    last_previewed = None

    # The placeholder to show in the command palette
    placeholder_ = None

    # The name of the arg to fill in
    arg_name = None

    # If the user is selecting the light or dark variant
    variant = False

    # The name of the setting to load the previous value for
    setting_name = None

    # The default value if the setting is missing
    default_value = None

    # The value to pre-select
    pre_selection = None

    # A string prefix to place before the selected value
    prefix = None

    def __init__(self, placeholder, arg_name, variant, setting_name, default_value, prefix):
        self.placeholder_ = placeholder
        self.arg_name = arg_name
        self.variant = variant
        self.setting_name = setting_name
        self.default_value = default_value
        self.prefix = prefix

    def name(self):
        return self.arg_name

    def placeholder(self):
        return self.placeholder_

    def cancel(self):
        self.prefs.set('theme', self.original)
        sublime.save_settings(PREFS_FILE)

    def description(self, v, text):
        if self.prefix:
            return self.prefix + text
        return text

    def next_input(self, args):
        if "name" in args and args["name"] == "auto":
            if "light" not in args:
                return ThemeInputHandler(
                    "Light variant",
                    "light",
                    True,
                    "light_theme",
                    "Default.sublime-theme",
                    "Light: "
                )
            elif "dark" not in args:
                return ThemeInputHandler(
                    "Dark variant",
                    "dark",
                    True,
                    "dark_theme",
                    "Default Dark.sublime-theme",
                    "Dark: "
                )
        else:
            None

    def preview(self, name):
        if name is None:
            return

        self.last_previewed = name

        def update_theme():
            # The color scheme to preview has been updated since
            # the timeout was created
            if name != self.last_previewed:
                return
            if self.prefs.get('theme') == name:
                return
            self.prefs.set('theme', name)
        sublime.set_timeout(update_theme, 250)

        return None

    def list_items(self):
        self.window = sublime.active_window()
        self.prefs = sublime.load_settings(PREFS_FILE)

        self.original = os.path.basename(
            self.prefs.get('theme', DEFAULT_THEME))
        self.pre_selection = os.path.basename(
            self.prefs.get(self.setting_name, self.default_value))

        items = []
        selected = -1

        if not self.variant:
            kind_info = sublime.KIND_AMBIGUOUS
            if self.pre_selection == "auto":
                kind_info = CURRENT_KIND
                selected = 0

            items.append(sublime.ListInputItem(
                'Auto',
                'auto',
                details='Switches between light and dark themes to match OS appearance',
                kind=kind_info
            ))

        nameset = set()

        for theme in sublime.find_resources('*.sublime-theme'):
            pkg, basename = os.path.split(theme)
            name, ext = os.path.splitext(basename)

            # Themes with the same name, but in different packages, are
            # considered a single logical theme, as the data from the
            # different files is merged. Ensure there's only one entry per
            # basename
            if name in nameset:
                continue
            nameset.add(name)

            kind_info = sublime.KIND_AMBIGUOUS
            if self.pre_selection and basename == self.pre_selection:
                selected = len(items)
                kind_info = CURRENT_KIND

            if pkg.startswith("Packages/"):
                pkg = pkg[len("Packages/"):]

            items.append(sublime.ListInputItem(name, basename, details=pkg, kind=kind_info))

        return (items, selected)


class ResourceNameInputHandler(sublime_plugin.ListInputHandler):
    def name(self):
        return "name"

    def placeholder(self):
        return "Name"

    def list_items(self):
        items = []
        for f in sublime.find_resources(''):
            if f.startswith("Packages/"):
                items.append(f[len("Packages/"):])
        return items


class ViewResourceCommand(sublime_plugin.WindowCommand):
    def run(self, name):
        self.window.run_command("open_file", {"file": "${packages}/" + name})

    def input(self, args):
        if "name" not in args:
            return ResourceNameInputHandler()
        else:
            return None


class CustomizeColorSchemeCommand(sublime_plugin.WindowCommand):
    def run(self):
        color_scheme = sublime.ui_info().get('color_scheme', {}).get('resolved_value')
        if color_scheme is None:
            color_scheme = DEFAULT_CS

        if '/' not in color_scheme:
            possible_paths = sublime.find_resources(color_scheme)
            default_path = 'Packages/Color Scheme - Default/' + color_scheme
            if default_path in possible_paths or len(possible_paths) == 0:
                color_scheme = default_path
            else:
                color_scheme = possible_paths[0]

        # Ensure we always create overrides with the .sublime-color-scheme ext
        user_package_path = os.path.join(sublime.packages_path(), 'User')
        color_scheme_file_name = os.path.basename(color_scheme)
        base_name, ext = os.path.splitext(color_scheme_file_name)
        if ext in {'.tmTheme', '.hidden-tmTheme', '.hidden-color-scheme'}:
            color_scheme_file_name = base_name + '.sublime-color-scheme'
        user_file = os.path.join(user_package_path, color_scheme_file_name)

        # edit_settings only works with ${packages}-based paths
        if color_scheme.startswith('Packages/'):
            color_scheme = '${packages}' + color_scheme[8:]

        self.window.run_command(
            'edit_settings',
            {
                "base_file": color_scheme,
                'user_file': user_file,
                "default":
                    "// Documentation at https://www.sublimetext.com/docs/color_schemes.html\n"
                    "{\n"
                    "\t\"variables\":\n"
                    "\t{\n"
                    "\t},\n"
                    "\t\"globals\":\n"
                    "\t{\n"
                    "\t},\n"
                    "\t\"rules\":\n"
                    "\t[\n"
                    "\t\t$0\n"
                    "\t]\n"
                    "}\n"
            })


class CustomizeThemeCommand(sublime_plugin.WindowCommand):
    def run(self):
        theme = sublime.ui_info().get('theme', {}).get('resolved_value')
        if theme is None:
            theme = DEFAULT_THEME

        if '/' not in theme:
            possible_paths = sublime.find_resources(theme)
            default_path = 'Packages/Theme - Default/' + theme
            if default_path in possible_paths or len(possible_paths) == 0:
                theme = default_path
            else:
                theme = possible_paths[0]

        # edit_settings only works with ${packages}-based paths
        if theme.startswith('Packages/'):
            theme = '${packages}' + theme[8:]

        self.window.run_command(
            'edit_settings',
            {
                "base_file": theme,
                "default":
                    "// Documentation at https://www.sublimetext.com/docs/themes.html\n"
                    "{\n"
                    "\t\"variables\":\n"
                    "\t{\n"
                    "\t},\n"
                    "\t\"rules\":\n"
                    "\t[\n"
                    "\t\t$0\n"
                    "\t]\n"
                    "}\n"
            })
