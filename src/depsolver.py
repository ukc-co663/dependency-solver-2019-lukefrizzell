import json
import sys
import re
import itertools

def parse_package(desc):
    ver_ops_regex = re.compile("([<>=]+)")

    splits = re.split(ver_ops_regex, desc)
    name = splits[0]

    ver = ''
    ver_ops = None

    if len(splits) > 1:
        ver = splits[2]
        ver_ops = splits[1]

    return [name, ver, ver_ops]


def parse_constraint(desc):
    op = desc[0]
    return [op] + parse_package(desc[1:])


def compare_sub_version(a, op, b):
    if op == '<':
        return a < b
    if op == '<=':
        return a <= b
    if op == '=':
        return a == b
    if op == '>=':
        return a >= b
    else:
        return a > b


def compare_version(a, op, b):
    if op is None:
        return True

    va = list(map(lambda x: int(x), a.split('.')))
    vb = list(map(lambda x: int(x), b.split('.')))

    la = len(va)
    lb = len(vb)

    while la < lb:
        va.append(0)

    while lb < la:
        vb.append(0)

    for i in range(len(va)):
        if not compare_sub_version(va[i], op, vb[i]):
            return False
    return True


def get_repo_matches(pkg, repo):
    repo_matches = [x for x in repo if x["name"] == pkg[0] and compare_version(x["version"], pkg[2], pkg[1])]
    return repo_matches


def get_package_string(name, version):
    return name + "=" + version


def flatten(package, repo):
    matches = get_repo_matches(package, repo)
    match_list = []
    for match in matches:
        p_str = get_package_string(match["name"], match["version"])
        deps = match.get("depends")
        conjs = []
        if deps:
            dep_list = []
            dep_list.append([p_str])
            for dep in deps:
                dep_opts = []
                for dep_opt in dep:
                    dms = get_repo_matches(parse_package(dep_opt), repo)
                    for dm in dms:
                        dep_opts.append(get_package_string(dm["name"], dm["version"]))
                dep_list.append(dep_opts)
            conjs = list(itertools.product(*dep_list))
        else:
            conjs.append([p_str])
        match_list.append(conjs)
    return match_list


def calculate_cost(option, repo):
    cost = 0
    for pkg in option:
        p = parse_package(pkg)
        matches = get_repo_matches(p, repo)
        cost += matches[0].get("size")
    return cost


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
options = []
for package in pkg_constraints:
    parsed = parse_constraint(package)
    if parsed[0] == '+':
        options.append(flatten(parsed[1:], pkg_repository))
    
commands = []
for package in options:
    packages = None
    new_cost = -1
    for option in package:
        items = option[0]
        cost = calculate_cost(items, pkg_repository)
        if packages == None:
            new_cost = cost
            packages = items
        else:
            if cost < new_cost:
                new_cost = cost
                packages = items
    commands += list(packages)

for i in range(len(commands)):
    commands[i] = "+"+commands[i]

print (json.dumps(commands))

