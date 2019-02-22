import json
import sys
import re
from satispy import Variable, Cnf
from satispy.solver import Minisat

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


def generate_clause(package):
    n, v, d, c = package
    v1 = Variable(n + '=' + v)
    exp = v1
    cjs = None
    for conj in d:
        djs = None
        for disj in conj:
	   if djs is None:
               djs = generate_clause(disj)
           else:
               djs = djs | (generate_clause(disj))
        if cjs is None:
            cjs = djs
        else:
            cjs = cjs & (djs)

    if cjs is None:
	return exp

    exp = exp & (cjs)
    return exp


def get_package_ref(pkg):
    n, v = pkg
    return "+"+n+"="+v


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

    solver = Minisat()
    
    exp = None
    for pkg in packages:
        opts = None
        for pkg_opt in pkg:
            if opts is None:
                opts = generate_clause(pkg_opt)
            else:
                opts = opts | (generate_clause(pkg_opt))
        if exp is None:
            exp = opts
        else:
            exp = exp & (opts)

    solution = solver.solve(exp)
   
    if not solution.success:
       print("Could not find solution")    

    print(solution)


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
# f = open("commands.json", "w")
# f.write(json.dumps(commands))


