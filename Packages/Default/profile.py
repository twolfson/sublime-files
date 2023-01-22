import sublime_api
import sublime_plugin


def format_details(count, max, sum):
    if count > 1:
        return "{0:.3f}s total, mean: {1:.3f}s, max: {2:.3f}s".format(
            sum,
            sum / count,
            max
        )
    elif count == 1:
        return "{0:.3f}s total".format(sum)
    else:
        return "0s total"


def profile_text():
    output = ""
    data = sublime_api.gather_plugin_profiling_data()
    last_event = None
    for row in sorted(data, key=lambda r: (r[0], r[1])):
        event = row[0]
        if event != last_event:
            if last_event:
                output += "\n"
            output += "{0}:\n".format(event)
        last_event = event
        output += "    {0}: {1}\n".format(
            row[1],
            format_details(row[2], row[3], row[4])
        )
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
