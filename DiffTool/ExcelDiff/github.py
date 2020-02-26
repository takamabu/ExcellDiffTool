# -*- coding: utf-8 -*-
from __future__ import print_function
from __future__ import unicode_literals

import contextlib
import sys
import textwrap
from distutils.command.config import config
from xml.sax.saxutils import escape

import six
from sxsdiff.generators import BaseGenerator

_html_escape_table = {
    ' ': "&nbsp;",
    '"': "&quot;",
    "'": "&apos;",
}


def html_escape(holder):
    return escape(six.text_type(holder), _html_escape_table)


class GitHubStyledGenerator(BaseGenerator):
    def __init__(self):
        self.buffer = ''

    def run(self, diff_result):
        super().run(diff_result)
        return self.buffer

    def _spit(self, content):
        self.buffer = self.buffer + content

    def visit_row(self, line_change):
        if not line_change.changed:
            self._spit_unchanged_side(
                'L', line_change.left_no, line_change.left)
            self._spit_unchanged_side(
                'R', line_change.right_no, line_change.right)
        else:
            self._spit_changed_side(
                'L', line_change.left_no, line_change.left)
            self._spit_changed_side(
                'R', line_change.right_no, line_change.right)

    @contextlib.contextmanager
    def wrap_row(self, line_change):
        self._spit('      <tr>')
        yield
        self._spit('      </tr>')

    @contextlib.contextmanager
    def wrap_result(self, sxs_result):
        self._spit(textwrap.dedent("""\
          <div class="container">
          <div class="file">
          <div class="data highlight blob-wrapper">
            <table class="diff-table file-diff-split">
            <tbody>"""
                                   ))

        yield

        self._spit(textwrap.dedent("""\
            </tbody>
            </table>
          </div>
          </div>
          </div>"""))

    def _spit_unchanged_side(self, side_char, lineno, holder):
        context = {
            'side_id': '%s%d' % (side_char, lineno),
            'mode': 'context',
            'lineno': lineno,
            'code': html_escape(holder),
        }
        self._spit_side_from_context(context)

    def _spit_changed_side(self, side_char, lineno, holder):
        if not holder:
            self._spit_empty_side()
            return

        bits = []
        for elem in holder.elements:
            piece = html_escape(elem)
            if elem.is_changed:
                bits.append('<span class="x x-first x-last">%s</span>' % piece)
            else:
                bits.append(piece)
        code = ''.join(bits)

        if side_char == 'L':
            mode = 'deletion'
        else:
            mode = 'addition'

        context = {
            'side_id': '%s%d' % (side_char, lineno),
            'mode': mode,
            'lineno': lineno,
            'code': code,
        }
        self._spit_side_from_context(context)

    def _spit_side_from_context(self, context):
        # Line number
        self._spit('      <td id="%(side_id)s" class="blob-num'
                   ' blob-num-%(mode)s base js-linkable-line-number"'
                   ' data-line-number="%(lineno)d"></td>' % context)
        # Code
        self._spit('      <td class="blob-code blob-code-%(mode)s base">'
                   '%(code)s</td>' % context)

    def _spit_empty_side(self):
        self._spit(
            '      <td class="blob-num blob-num-empty head empty-cell"></td>')
        self._spit(
            '      <td class="blob-code blob-code-empty head empty-cell"></td>')
