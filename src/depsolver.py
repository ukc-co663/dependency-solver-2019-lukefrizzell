import json
import sys
import re


def find_in_repo(c, p):
    for entry in p:
        if entry['name'] is c[0]:
            return entry


def parse_package(desc):
    ver_ops_regex = re.compile("([<>=]+)")

    splits = re.split(ver_ops_regex, desc)
    name = splits[0]

    ver = []
    ver_ops = None

    if len(splits) > 1:
        ver = splits[2].split()
        ver_ops = splits[1]

    return [name, ver, ver_ops]


def parse_constraint(desc):
    # valid_regex = re.compile('^[\+\-][.+a-zA-Z0-9-]+(<|>)?=?(\d+(.\d+)*)$')
    # if not valid_regex.match(cmd_str):
    #     return

    op = desc[0]
    return [op] + parse_package(desc[1:])


def compare_version(a, op, b):
    if op is None:
        return True
    if op is '<':
        return a < b
    if op is '<=':
        return a <= b
    if op is '=':
        return a == b
    if op is '>=':
        return a >= b
    else:
        return a > b


def install_map(pkg, repo):
    package = []
    repo_matches = [x for x in repo if x["name"] == pkg[0]
                    and compare_version(x["version"].split(), pkg[2], pkg[1])]
    for match in repo_matches:
        deps = []
        confs = []
        if match.get("depends") is not None:
            for dep in match["depends"]:
                for dep_opt in dep:
                    deps.append(install_map(parse_package(dep_opt), repo))
        if match.get("conflicts") is not None:
            for conf in match["conflicts"]:
                confs.append(conf)
        package.append((match["name"], match["version"], deps, confs))
    return package


def calculate_state(constr, repo, init):
    packages = []
    for package in constr:
        parsed_package = parse_constraint(package)
        if parsed_package[0] is '+':
            packages.append(install_map(parsed_package[1:], repo))

    print(packages)


if len(sys.argv) < 4:
    print("Argument count mismatch: required 3, actual", len(sys.argv) - 1)
    exit()

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

calculate_state(pkg_constraints, pkg_repository, pkg_initial)
