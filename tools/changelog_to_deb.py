#!/usr/bin/env python3

import argparse
import datetime
import re

VERSION_HEADER_RE = re.compile(r'(?P<version>\d+\.\d+\.\d+) ?- ?(?P<date>\d{4}-\d{2}-\d{2})')
CHANGE_TYPE_RE = re.compile(r'^### ?(?P<change_type>.*)')
SKIP_LINE_RE = re.compile(r'^-{2,}|^$')
LIST_LINE_RE = re.compile(r'^[-*] ?(?P<line_item>.*)')
CONTINUATION_LINE_RE = re.compile(r'^ {1,4}.*')
# This date format doesn't include the timezone, since we just hard-code that
# to +0000
PARTIAL_DATE_FORMAT = '%a, %d %b %Y %H:%M:%S'


def main():
    args = get_args()
    with open(args.changelog) as fh:
        source_changelog = fh.read()
    new_changelog = convert_changelog(source_changelog, args.project, args.author,
        args.author_email)
    print(new_changelog, end='')


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('changelog')
    parser.add_argument('project')
    parser.add_argument('author')
    parser.add_argument('author_email')
    return parser.parse_args()


def convert_changelog(changelog, project_name, author, author_email):
    def finish_changeset():
        if not changeset_date:
            return
        date = changeset_date.strftime(PARTIAL_DATE_FORMAT) + ' +0000'
        changesets.append('\n -- %s <%s>  %s\n' % (author, author_email, date))

    new_changelog = []
    changesets = []
    changes = []
    current_change_type = None
    has_found_first_change = False
    changeset_date = None
    for line in changelog.split('\n'):
        version_header_match = VERSION_HEADER_RE.search(line)

        if version_header_match:
            # Start parsing a new section, finishing up the old one
            if has_found_first_change:
                finish_changeset()

            has_found_first_change = True

            current_change_type = None
            version = version_header_match.group('version')
            changeset_date_raw = version_header_match.group('date')
            changeset_date = datetime.datetime.strptime(changeset_date_raw, '%Y-%m-%d') + datetime.timedelta(hours=12)
            changesets.append('%s (%s) unstable; urgency=low\n' % (project_name, version))
            continue

        if not has_found_first_change:
            continue

        change_type_match = CHANGE_TYPE_RE.match(line)
        if change_type_match:
            current_change_type = change_type_match.group('change_type')
            continue

        line = line.rstrip()

        skip_match = SKIP_LINE_RE.match(line)
        if skip_match:
            continue

        line_item_match = LIST_LINE_RE.match(line)
        if line_item_match:
            line = line_item_match.group('line_item')

        is_continuation = CONTINUATION_LINE_RE.match(line)
        if current_change_type and not is_continuation:
            changesets.append('  * %s: %s' % (current_change_type, line))
        else:
            changesets.append('  %s' % line)

    finish_changeset()

    new_changelog.append('\n'.join(changesets))
    ret = ''.join(new_changelog)
    return ret


if __name__ == '__main__':
    main()
