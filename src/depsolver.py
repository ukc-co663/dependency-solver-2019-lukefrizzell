import json
import sys
import re
import itertools


repo = []


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


def get_repo_matches(pkg):
    repo_matches = [x for x in repo if x["name"] == pkg[0] and compare_version(x["version"], pkg[2], pkg[1])]
    return repo_matches


def get_package_string(name, version):
    return name + "=" + version


def flatten(package):
    matches = get_repo_matches(package)
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
                    dms = get_repo_matches(parse_package(dep_opt))
                    for dm in dms:
                        dep_opts.append(get_package_string(dm["name"], dm["version"]))
                dep_list.append(dep_opts)
            conjs = list(itertools.product(*dep_list))
        else:
            conjs.append([p_str])
        match_list.append(conjs)
    return match_list


def calculate_cost(option):
    cost = 0
    for pkg in option[0]:
        p = parse_package(pkg)
        matches = get_repo_matches(p)
        cost += matches[0].get("size")
    return cost


def has_conflict(option):
    option = option[0]
    for pkg in option:
        p = parse_package(pkg)
        matches = get_repo_matches(p)
        conf = matches[0].get("conflicts")
        if conf:
            for c in conf:
                p_c = parse_package(c)
                for opt in option:
                    if opt is pkg:
                        continue
                    p_o = parse_package(opt)
                    if p_o[0] == p_c[0]:
                        if compare_version(p_o[1], p_c[2], p_c[1]):
                            return True
    return False


if len(sys.argv) < 4:
    print("Argument count mismatch: required 3, actual", len(sys.argv) - 1)
    exit()

f = open(sys.argv[1], "r")
repository_json = f.read()
repo = json.loads(repository_json)

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
        options.append(flatten(parsed[1:]))
    
commands = []
for package in options:
    package.sort(key=calculate_cost)	
    i = 0
    while has_conflict(package[i]):
        i += 1    
        if i >= len(package):
	    print("Uh Oh")

    commands += package[i][0]
    

for i in range(len(commands)):
    commands[i] = "+" + commands[i]

print (json.dumps(commands))

