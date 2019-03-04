import json
import sys
import re
import itertools


repo = []
avoids = []

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

    i = 0
    while i < len(va):
        if va[i] == vb[i]:
            i += 1
            continue
        if not compare_sub_version(va[i], op, vb[i]):
            return False
        else:
            return True
    if '=' in op:
        return True    
    return False


def get_repo_matches(pkg):
    repo_matches = [x for x in repo if x["name"] == pkg[0] and compare_version(x["version"], pkg[2], pkg[1])]
    return repo_matches


def get_package_string(name, version):
    return name + "=" + version


def flatten(item):
    output = []
    if type(item) is list:
        for i in item:
            output += flatten(i)
    else: 
        output = [item]
    return output


def remove_duplicates(item):
    output = []
    for i in item:
       if i not in output: 
           output.append(i)
    return output


def solve(package, roots):
    matches = get_repo_matches(package)
    match_list = []
    for match in matches:
        p_str = get_package_string(match["name"], match["version"])
        
        if p_str in roots:
           continue

        deps = match.get("depends")
        if deps:
            dep_list = []
            conjs = []
            for dep in deps:
                dep_opts = []
                for dep_opt in dep:
                    p_d = parse_package(dep_opt)
                    s = solve(p_d, roots + [p_str])
                    for item in s:
			dep_opts.append(item)
		dep_list.append(dep_opts)
            conjs += list(itertools.product(*dep_list))             
	    for item in conjs:
	        match_list.append(list(item) + [p_str])
        else:
            match_list.append([p_str])
    return match_list


def calculate_cost(option):
    cost = 0
    for pkg in option: 
        p = parse_package(pkg)
        matches = get_repo_matches(p)
        cost += matches[0].get("size")
    return cost


def has_conflict(option, init, avoids):
    for pkg in option:
        p = parse_package(pkg)
        matches = get_repo_matches(p)
        conf = matches[0].get("conflicts")
        if conf:
            for c in conf:
                p_c = parse_package(c)
                for opt in list(option) + init:
                    if opt is pkg:
                        continue
                    p_o = parse_package(opt)
                    if p_o[0] == p_c[0]:
                        if compare_version(p_o[1], p_c[2], p_c[1]):
                            #print(get_package_string(p_o[0], p_o[1]), p_c[2], get_package_string(p_c[0], p_c[1]))
                            return True
        for a in avoids:
	    if p[0] == a[0]:
                if compare_version(p[1], a[2], a[1]):
                    return True
    return False


def remove_conflicts(package, init):
    i = 0
    while i < len(package):
        if has_conflict(package[i], init, avoids):
            i += 1
        else:
            return package[i]
    for u in init:
        i = 0
        tmp = init
        tmp.remove(u)
        while i < len(package):
            if has_conflict(package[i], tmp, avoids + [parse_package(u)]):
                i += 1
            else: 
                avoids.append(parse_package(u))
                return package[i]


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
install = []
for package in pkg_constraints:
    parsed = parse_constraint(package)
    if parsed[0] == '+':
        install.append(parsed[1:])
    else:
        avoids.append(parsed[1:])

i_list = []
options = []
for i in install:
    opts = []
    s = solve(i, [])
    for item in s:
        opts.append(item)
    i_list.append(opts)
options += list(map(list, itertools.product(*i_list)))

commands = []

package = map(flatten, options)    

package.sort(key=calculate_cost)	
result = remove_conflicts(package, pkg_initial)    
  
commands += result

for i in range(len(commands)):
    commands[i] = "+" + commands[i]

commands = remove_duplicates(commands)

for a in avoids:
    commands = ["-"+ get_package_string(a[0], a[1])] + commands

print (json.dumps(commands))

