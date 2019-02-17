import json
import sys
import re


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


def install_map(pkg, repo):
    package = []
    repo_matches = [x for x in repo if x["name"] == pkg[0] and compare_version(x["version"], pkg[2], pkg[1])]
    for match in repo_matches:
        deps = []
        conflicts = []
        if match.get("depends") is not None:
            for dep in match["depends"]:
                x = []
                for dep_opt in dep:
                    x += install_map(parse_package(dep_opt), repo)
                deps.append(x)

        if match.get("conflicts") is not None:
            for conf in match["conflicts"]:
                conflicts.append(conf)
        package.append((match["name"], match["version"], deps, conflicts))
    return package


def get_package_ref(pkg):
    n, v = pkg
    return "+"+n+"="+v


def process_package_options(package_opt, current):
    name, version, depends, conflicts = package_opt
    if conflicts:
        for conflict in conflicts:
            p_conflict = parse_package(conflict)
            for c in current:
                n, v, d, conf = c
                if p_conflict[0] == n:
                    if compare_version(v, p_conflict[2], p_conflict[1]):
                        return []
    for c in current:
        n, v, d, conf = c
        for con in conf:
            p_conf = parse_package(con)
            if name == p_conf[0]:
                if compare_version(version, p_conf[2], p_conf[1]):
                    return []

    this_package = [(name, version)]
    result = process_installation(depends, current)
    if result:
        this_package.append(result)
    return this_package


def process_package(package, current):
    output = []
    for option in package:
        result = process_package_options(option, current)
        if result:
            output.append(result)
    return output


def process_installation(packages, current):
    output = []
    for package in packages:
        if len(packages) > 1:
            for package2 in packages:
                if package == package2:
                    continue
                else:
                    for opt in package2:
                        n, v, d, c = opt
                        r = process_package(package, current + [(n, v, d, c)])
                        if r:
                            output.append(r)
        else:
            result = process_package(package, current)
            if not result:
                return []
            else:
                output.append(result)
    return output


def init_to_current(init):
    output = []
    for i in init:
        p_i = parse_package(i)
        output.append((p_i[0], p_i[1]))
    return output


def state_to_commands(state):
    output = []
    for st in state:
        if st:
            if type(st) is tuple:
                output.append(get_package_ref(st))
            else:
                output += state_to_commands(st)
    return output


def calculate_state(constr, repo):
    packages = []
    uninstall_packages = []
    for package in constr:
        parsed_package = parse_constraint(package)
        if parsed_package[0] == '+':
            packages.append(install_map(parsed_package[1:], repo))
        else:
            uninstall_packages.append(parse_package(package))

    installation = process_installation(packages, init_to_current(pkg_initial))
    print(state_to_commands(installation))


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

calculate_state(pkg_constraints, pkg_repository)


