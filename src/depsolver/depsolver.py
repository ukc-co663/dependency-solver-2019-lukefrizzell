import json
import sys
import re


def parse_cmd(cmd_str):

    valid_regex = re.compile('[\+\-][.+a-zA-Z0-9-]+=(\d+(.\d)*)')
    if not valid_regex.match(cmd_str):
        return

    op_regex = re.compile('[\+\-]')
    name_regex = re.compile('(?<=[\+\-])[.+a-zA-Z0-9-]+')
    ver_regex = re.compile('(?<==)(\d+(.\d)*)')

    op = op_regex.search(cmd_str).group()
    name = name_regex.search(cmd_str).group()
    ver = ver_regex.search(cmd_str).group().split('.')

    return [op, name, ver]


def install(args):
    print('installing:', args[0], 'version', str.join('.', args[1]))


def uninstall(args):
    print('uninstalling:', args[0], 'version: ', str.join('.', args[1]))


if len(sys.argv) < 2:
    print('Please provide a package.json')

f = open(sys.argv[1], "r")
pkg_json = f.read()
pkg_cmd_strs = json.loads(pkg_json)

for cmd_str in pkg_cmd_strs:
    pkg_cmd = parse_cmd(cmd_str)
    if pkg_cmd is None:
        print(cmd_str, 'is not a valid command')
        continue
    if pkg_cmd[0] is '+':
        install(pkg_cmd[1:])
    else:
        uninstall(pkg_cmd[1:])
