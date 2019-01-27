import json
import sys
import re


def find_in_repo(cmd, pkg_repository):
    for entry in pkg_repository:
        if entry['name'] is cmd[0]:
            return entry


def parse_package(desc):
    ver_ops_regex = re.compile('([<>=]+)')

    splits = re.split(ver_ops_regex, desc)
    name = splits[0]

    ver = []
    ver_ops = None

    if len(splits) > 1:
        ver = splits[2]
        ver_ops = splits[1]

    return [name, ver, ver_ops]


def parse_constraint(desc):
    # valid_regex = re.compile('^[\+\-][.+a-zA-Z0-9-]+(<|>)?=?(\d+(.\d+)*)$')
    # if not valid_regex.match(cmd_str):
    #     return

    op = desc[0]
    return [op] + parse_package(desc[1:])


def install(cmd, pkg_repository):
    if cmd[2] is None:
        version = 'any'
    else:
        version = cmd[2] + cmd[1]

    print('installing:', cmd[0], '-> version:', version)

    repository_entry = find_in_repo(cmd, pkg_repository)
    if 'depends' in repository_entry:
        for dep in repository_entry['depends']:
            i = 0
            satisfied = False
            while not satisfied and i < len(dep):
                pkg = parse_package(dep[i])
                if install(pkg, pkg_repository):
                    satisfied = True
                else:
                    i += 1
            if not satisfied:
                return False

    return True


def uninstall(args):
    if args[2] is None:
        version = 'any'
    else:
        version = args[2] + args[1]

    print('uninstalling:', args[0], '-> version:', version)


f = open(sys.argv[1], "r")
repository_json = f.read()
pkg_repository = json.loads(repository_json)

f = open(sys.argv[2], "r")
initial_json = f.read()
pkg_initial = json.loads(initial_json)

f = open(sys.argv[3], "r")
constraints_json = f.read()
pkg_constraints = json.loads(constraints_json)

for constraint in pkg_constraints:
    cmd = parse_constraint(constraint)
    if cmd is None:
        print(cmd, 'is not a valid command')
        continue

    if cmd[0] is '+':
        install(cmd[1:], pkg_repository)
    else:
        uninstall(cmd[1:])
