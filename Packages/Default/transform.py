import codecs
import string

import sublime_plugin


class Transformer(sublime_plugin.TextCommand):
    def run(self, edit):
        view = self.view
        for s in view.sel():
            if s.empty():
                s = view.word(s)

            txt = self.transformer(view.substr(s))
            view.replace(edit, s, txt)


class SwapCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return s.swapcase()


class UpperCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return s.upper()


class LowerCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return s.lower()


class TitleCaseCommand(Transformer):
    @staticmethod
    def transformer(s):
        return string.capwords(s, " ")


class Rot13Command(Transformer):
    @staticmethod
    def transformer(s):
        return codecs.encode(s, 'rot-13')
