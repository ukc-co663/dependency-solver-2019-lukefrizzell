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
    n, v, d, c = pkg
    return "+"+n+"="+v


def find_state(packages, curr):
    for pkg_opt in packages:
        name, v, d, c = pkg_opt
        result = []

        conflicts = conflict_check(pkg_opt, curr)
        result += [pkg_opt]

        if not d:
            return result

        r = []
        for i in range(len(d)):
            for dep in d[i]:
                if dep in conflicts:
                    continue
            new_curr = curr
            new_curr.append(get_package_ref(pkg_opt))
            r += find_state(d[i], new_curr)
        if len(r) == len(d):
            return result + r
    return []


def calculate_state(constr, repo, init):
    packages = []
    uninstall_packages = []
    for package in constr:
        parsed_package = parse_constraint(package)
        if parsed_package[0] == '+':
            packages.append(install_map(parsed_package[1:], repo))
        else:
            uninstall_packages.append(parse_package(package))

    print(packages)
    for pkg in packages:
        for a in find_state(pkg, init):
            if a:
                n, v, d, c = a
                print(n, v)


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

print(conflict_check(('A', '2.01', [[('B', '3.2', [], ['B<3.2']), ('C', '1', [], ['B'])], [('D', '10.3.1', [], ['B>=3.1'])]], []), []))

