#!/usr/bin/env python3
from collections import OrderedDict
from pathlib import Path
import xlrd
import yaml
from jinja2 import Template
from sxsdiff import DiffCalculator
from ExcelDiff.github import GitHubStyledGenerator
from optparse import OptionParser


def _parse_options():
    usage = ('Get diff of 2 excel file'
             'Usage examples:\n'
             '  %prog a.xlsx b.xlsx'
             )
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    if len(args) < 2:
        parser.error('Two excel file path is required')
    return options, args


def _get_value_collumns(path, row_num):
    book_old = xlrd.open_workbook(path)
    sheet_old = book_old.sheet_by_index(0)
    dTitle = dict()
    for col_num in range(1, sheet_old.ncols):
        dTitle [sheet_old.cell_value(0, col_num).strip()] = sheet_old.cell_value(row_num, col_num)
    dTitle ['row'] = row_num + 1
    return dTitle


def excel_diff(path_old, path_new, collumn_expect):
    book_old = xlrd.open_workbook(path_old)
    sheet_old = book_old.sheet_by_index(0)

    book_new = xlrd.open_workbook(path_new)
    sheet_new = book_new.sheet_by_index(0)

    diff_table = OrderedDict()
    for rx in range(1, sheet_old.nrows):
        test_id = sheet_old.cell_value(rx, 0).strip()
        if not test_id:
            continue
        dValue_old = _get_value_collumns(path_old, rx)
        diff_table[test_id] = {
            'id': test_id,
            'A': {e : dValue_old[e] for e in dValue_old}
        }

    for rx in range(1, sheet_new.nrows):
        test_id = sheet_new.cell_value(rx, 0)
        if not test_id:
            continue
        dValue_new = _get_value_collumns(path_new, rx)
        if test_id not in diff_table:
            diff_table[test_id] = {
                'id': test_id
            }
        diff_table[test_id]['B'] = {e : dValue_new[e] for e in dValue_new}

    # Get Diff
    for i in diff_table:
        if 'A' not in diff_table[i]:
            diff_table[i]['diff'] = 'New test case'
            continue

        if 'B' not in diff_table[i]:
            diff_table[i]['diff'] = 'Removed test case'
            continue
        for e in collumn_expect:           
            if diff_table[i]['A'][e] != diff_table[i]['B'][e] and e in list(diff_table[i]['B'].keys()):
                diff_table[i]['diff'] = 'Found'
                sxsdiff_result = DiffCalculator().run(diff_table[i]['A'][e], diff_table[i]['B'][e])
                diff_table[i]['diff_' + e.replace(' ', '_')] = GitHubStyledGenerator().run(sxsdiff_result)
            else:
                diff_table[i]['A'][e] = ''
                diff_table[i]['B'][e] = ''
    payload = {
        'file': [
            path_old.name, path_new.name
        ],
        'navbar' : [e for e in collumn_expect],
        'data': diff_table
    }
    with open('diff.yaml', 'w') as f:
        f.write(yaml.dump(payload, default_flow_style=False))

    return payload


def generate_report(payload):
    with open('template.html', 'r') as f:
        template_raw = f.read()
    t = Template(template_raw)
    return t.render(**payload)


def main():
    opts, args = _parse_options()
    file_a = Path(args[0])
    file_b = Path(args[1])
    collumn_expect = args[2:]
    print('%s VS %s' % (file_a, file_b))
    print('> Calculating diff...')
    payload = excel_diff(file_a, file_b, collumn_expect)
    print('> Generate repo...')
    result = generate_report(payload)
    with open('result.html', 'w') as f:
        f.write(result)

    print('Done.')




if __name__ == '__main__':
    main()
