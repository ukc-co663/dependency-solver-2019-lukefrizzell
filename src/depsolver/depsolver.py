import json
import sys
import re


def parse_cmd(cmd_str):
    # valid_regex = re.compile('^[\+\-][.+a-zA-Z0-9-]+(<|>)?=?(\d+(.\d+)*)$')
    # if not valid_regex.match(cmd_str):
    #     return

    ver_ops_regex = re.compile('([<>=]+)')

    op = cmd_str[0]
    splits = re.split(ver_ops_regex, cmd_str[1:])
    name = splits[0]
    ver = splits[2].split('.')
    ver_ops = splits[1]

    return [op, name, ver, ver_ops]


def install(args):
    print('installing:', args[0], 'version', args[2], args[1])


def uninstall(args):
    print('uninstalling:', args[0], 'version', args[2], args[1])


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
