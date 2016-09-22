import sublime_plugin


def profile_text():
    output = ""
    for event in sorted(sublime_plugin.profile.keys()):
        output += "{0}:\n".format(event)
        for name, summary in sublime_plugin.profile[event].items():
            output += "    {0}: {1}\n".format(name, summary)
        output += "\n"
    return output


class ProfilePluginsCommand(sublime_plugin.WindowCommand):
    def run_(self, edit_token, args):
        output = "This list shows how much time each plugin has taken to respond to each event:\n\n"
        output += profile_text()

        v = self.window.new_file()
        v.set_scratch(True)
        v.set_name('Plugin Event Profile')
        edit = v.begin_edit(edit_token, "")
        v.insert(edit, 0, output)
        v.end_edit(edit)
