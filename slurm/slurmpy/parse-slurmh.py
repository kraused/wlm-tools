
import sys
import os
import re
import json
import hashlib

# Parse type + name tuples. This function is used to scan function arguments as well
# as structure members.
def parseTypeNameList(text, sep):
	members = []

	for p in re.sub(r'\s', ' ', text).split(sep):
		if '...' == p.strip():	# variable arguments (funcction parameter)
			members += [('?', '')]
		else:
			lst = [x.strip() for x in list(re.compile(r'([a-zA-Z0-9_\*\[\]]+)').findall(p))]

			if 0 == len(lst):
				continue

			# Shift pointers from the name to the type
			while (len(lst[-1]) > 0) and ('*' == lst[-1][0]):
				lst[-2] += '*'
				lst[-1]  = lst[-1][1:]

			lst0 = ' '.join(lst[:-1])
			lst1 = lst[-1]

			if '' == lst0:
				lst0 = lst1
				lst1 = ''
			if 'void' == lst0:
				continue

			members += [(lst0, lst1)]

	return members

def getFunctionList(text):
	fcts = []

	rx = re.compile(r'extern\s?([a-zA-Z0-9_ \*]+?)([a-zA-Z0-9_]+)\s+PARAMS\(\s*\((.*?)\)\s*\)\s*;', re.MULTILINE | re.DOTALL)
	for f in rx.findall(text):
		fcts += [(f[0].strip(), f[1].strip(), parseTypeNameList(f[2], ','))]

	return fcts

def getEnumList(text):
	enums = []

	rx1 = re.compile(r'typedef\s+enum\s+([a-zA-Z0-9_]+)\s*\{(.*?)\}\s*([a-zA-Z0-9_]+)\s*;', re.MULTILINE | re.DOTALL)
	rx2 = re.compile(r'enum\s+([a-zA-Z0-9_]+)\s*\{([^\}]+)\}\s*;', re.MULTILINE | re.DOTALL)
	rx3 = re.compile(r'enum\s*\{([^\}]+)\}\s*;', re.MULTILINE | re.DOTALL)

	for name, x, typedef in rx1.findall(text):
		values = [u for u in map(lambda z: re.sub(r'\s*=\s*[0-9a-fA-Fx]*', '', z).strip(), x.split(',')) if u]
		enums += [(name, values, typedef)]
	for name, x          in rx2.findall(text):
		values = [u for u in map(lambda z: re.sub(r'\s*=\s*[0-9a-fA-Fx]*', '', z).strip(), x.split(',')) if u]
		enums += [(name, values, '')]
	for x                in rx3.findall(text):
		values = [u for u in map(lambda z: re.sub(r'\s*=\s*[0-9a-fA-Fx]*', '', z).strip(), x.split(',')) if u]
		enums += [('', values, '')]

	return enums

def getDefinesList(text):
	defines = []

	rx = re.compile(r'#\s*define\s+([a-zA-Z_0-9]+)\s+([0-9a-fA-Fx\-]+)\s*\n')
	for name, value in rx.findall(text):
		defines += [(name, value)]

	return defines

def md5sum(text):
	x = hashlib.md5()
	x.update(text)

	return x.hexdigest()

def getStructsList(text):
	structs = []

	rx1 = re.compile(r'typedef\s+struct\s+([a-zA-Z0-9_]*)\s*\{(.*?)\}\s*([a-zA-Z0-9_]+)\s*;', re.MULTILINE | re.DOTALL)
	rx2 = re.compile(r'typedef\s+struct\s+([a-zA-Z0-9_]*)\s+([a-zA-Z0-9_]+)\s*;', re.MULTILINE | re.DOTALL)

	for name, x, typedef in rx1.findall(text):
		if '' == name:
			name = "anon" + md5sum(x)

		structs += [(name, parseTypeNameList(x, ';'), typedef)]
	for name, typedef in rx2.findall(text):
		if '' == name:
			name = "anon" + md5sum(x)

		found = False
		for i, (other1, other2, other3) in enumerate(structs):
			if other1 == name:
				found = True
				if '' == other3:
					structs[i] = (other1, other2, other3)
				else:
					print("FIXME")
					print((name, typedef), (other1, other2, other3))

		if not found:
			structs += [(name, [], typedef)]

	return structs

text = ""
for f in sys.argv[1:-1]:
	text += open(f, "r").read()

# Get rid of comments
text = re.sub(re.compile(r'\/\*.*?\*\/', re.MULTILINE | re.DOTALL), '', text)
# Undo explicit line break
text = re.sub(re.compile(r'\\\s*\n'), '', text)
# Streamline whitespcea
text = re.sub(re.compile(r'[ \t\r\f\v]'), ' ', text)


api = {"enums": [], "defines": [], "structs": [], "functions": []}

for e in getEnumList(text):
	d = {"name": e[0], "members": e[1]}
	if len(e[2]) > 0:
		d["typedef"] = e[2]

	api["enums"] += [d]

for d in getDefinesList(text):
	d = {"name": d[0], "value": d[1]}

	api["defines"] += [d]

for s in getStructsList(text):
	d = {"name": s[0], "members": [], "typedef": s[2]}
	for t, n in s[1]:
		d["members"] += [{"type": t, "name": n}]

	api["structs"] += [d]

for f in getFunctionList(text):
	d = {"name": f[1], "retVal": f[0], "args": []}
	for t, n in f[2]:
		d["args"] += [{"type": t, "name": n}]

	api["functions"] += [d]

with open(sys.argv[-1], "w") as f:
	f.write(json.dumps(api))

