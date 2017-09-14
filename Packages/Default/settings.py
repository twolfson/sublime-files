import os.path

import sublime
import sublime_plugin


class EditSettingsCommand(sublime_plugin.ApplicationCommand):
    def run(self, base_file, user_file=None, default=None):
        """
        :param base_file:
            A unicode string of the path to the base settings file. Typically
            this will be in the form: "${packages}/PackageName/Package.sublime-settings"

        :param user_file:
            An optional file path to the user's editable version of the settings
            file. If not provided, the filename from base_file will be appended
            to "${packages}/User/".

        :param default:
            An optional unicode string of the default contents if the user
            version of the settings file does not yet exist. Use "$0" to place
            the cursor.
        """

        if base_file is None:
            raise ValueError('No base_file argument was passed to edit_settings')

        platform_name = {
            'osx': 'OSX',
            'windows': 'Windows',
            'linux': 'Linux',
        }[sublime.platform()]

        variables = {
            'packages': '${packages}',
            'platform': platform_name,
        }

        base_file = sublime.expand_variables(base_file.replace('\\', '\\\\'), variables)
        if user_file is not None:
            user_file = sublime.expand_variables(user_file.replace('\\', '\\\\'), variables)

        base_path = base_file.replace('${packages}', 'res://Packages')
        is_resource = base_path.startswith('res://')
        file_name = os.path.basename(base_file)
        resource_exists = is_resource and base_path[6:] in sublime.find_resources(file_name)
        filesystem_exists = (not is_resource) and os.path.exists(base_path)

        if not resource_exists and not filesystem_exists:
            sublime.error_message('The settings file "' + base_path + '" could not be opened')
            return

        if user_file is None:
            user_package_path = os.path.join(sublime.packages_path(), 'User')
            user_file = os.path.join(user_package_path, file_name)

            # If the user path does not exist, and it is a supported
            # platform-variant file path, then try and non-platform-variant
            # file path.
            if not os.path.exists(os.path.join(user_package_path, file_name)):
                for suffix in {'.sublime-keymap', '.sublime-mousemap', '.sublime-menu'}:
                    platform_suffix = ' (%s)%s' % (platform_name, suffix)
                    if not file_name.endswith(platform_suffix):
                        continue
                    non_platform_file_name = file_name[:-len(platform_suffix)] + suffix
                    non_platform_path = os.path.join(user_package_path, non_platform_file_name)
                    if os.path.exists(non_platform_path):
                        user_file = non_platform_path
                        break

        sublime.run_command('new_window')
        new_window = sublime.active_window()

        new_window.run_command(
            'set_layout',
            {
                'cols': [0.0, 0.5, 1.0],
                'rows': [0.0, 1.0],
                'cells': [[0, 0, 1, 1], [1, 0, 2, 1]]
            })
        new_window.focus_group(0)
        new_window.run_command('open_file', {'file': base_file})
        new_window.focus_group(1)
        new_window.run_command('open_file', {'file': user_file, 'contents': default})

        new_window.set_tabs_visible(True)
        new_window.set_sidebar_visible(False)

        base_view = new_window.active_view_in_group(0)
        user_view = new_window.active_view_in_group(1)

        base_settings = base_view.settings()
        base_settings.set('edit_settings_view', 'base')
        base_settings.set('edit_settings_other_view_id', user_view.id())

        user_settings = user_view.settings()
        user_settings.set('edit_settings_view', 'user')
        user_settings.set('edit_settings_other_view_id', base_view.id())
        if not os.path.exists(user_file):
            user_view.set_scratch(True)
            user_settings.set('edit_settings_default', default.replace('$0', ''))


class EditSyntaxSettingsCommand(sublime_plugin.WindowCommand):
    """
    Opens the syntax-specific settings file for the currently active view
    """

    def run(self):
        view = self.window.active_view()
        syntax, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        self.window.run_command(
            'edit_settings',
            {
                'base_file': '${packages}/Default/Preferences.sublime-settings',
                'user_file': os.path.join(sublime.packages_path(), 'User', syntax + '.sublime-settings'),
                'default': (
                    '// These settings override both User and Default settings '
                    'for the %s syntax\n{\n\t$0\n}\n') % syntax
            })

    def is_enabled(self):
        return self.window.active_view() is not None


class EditSettingsListener(sublime_plugin.EventListener):
    """
    Closes the base and user settings files together, and then closes the
    window if no other views are opened
    """

    def on_modified(self, view):
        """
        Prevents users from editing the base file
        """

        view_settings = view.settings()

        settings_view_type = view_settings.get('edit_settings_view')

        # If any edits are made to the user version, we unmark it as a
        # scratch view so that the user is prompted to save any changes
        if settings_view_type == 'user' and view.is_scratch():
            file_region = sublime.Region(0, view.size())
            if view_settings.get('edit_settings_default') != view.substr(file_region):
                view.set_scratch(False)

    def on_pre_close(self, view):
        """
        Grabs the window id before the view is actually removed
        """

        view_settings = view.settings()

        if not view_settings.get('edit_settings_view'):
            return

        if view.window() is None:
            return

        view_settings.set('window_id', view.window().id())

    def on_close(self, view):
        """
        Closes the other settings view when one of the two is closed
        """

        view_settings = view.settings()

        if not view_settings.get('edit_settings_view'):
            return

        window_id = view_settings.get('window_id')
        window = None
        for win in sublime.windows():
            if win.id() == window_id:
                window = win
                break

        if not window:
            return

        other_view_id = view_settings.get('edit_settings_other_view_id')
        views = window.views()
        views_left = len(views)
        for other in views:
            if other.id() == other_view_id:
                window.focus_view(other)
                # Prevent the handler from running on the other view
                other.settings().erase('edit_settings_view')
                # Run after timeout so the UI doesn't block with the view half closed
                sublime.set_timeout(lambda: window.run_command("close"), 50)

        # Don't close the window if the user opens another view in the window
        # or adds a folder, since they likely didn't realize this is a settings
        # window
        if views_left == 1 and len(window.folders()) < 1:
            # If the user closes the window containing the settings views, and
            # this is not delayed, the close_window command will be run on any
            # other window that is open.
            def close_window():
                if window.id() == sublime.active_window().id():
                    window.run_command("close_window")
            sublime.set_timeout(close_window, 50)


class OpenFileSettingsCommand(sublime_plugin.WindowCommand):
    """
    Old syntax-specific settings command - preserved for backwards compatibility
    """

    def run(self):
        view = self.window.active_view()
        settings_name, _ = os.path.splitext(os.path.basename(view.settings().get('syntax')))
        dir_name = os.path.join(sublime.packages_path(), 'User')
        self.window.open_file(os.path.join(dir_name, settings_name + '.sublime-settings'))

    def is_enabled(self):
        return self.window.active_view() is not None
