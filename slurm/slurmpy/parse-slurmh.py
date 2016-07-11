
import sys
import os
import re
import json
import subprocess

import plugin

# Get the absolute path of cc1 and try to guess the include path based on that. This works on my Arch
# box but not on Fedora.
def getIncludePathFromCc1():
	p = subprocess.Popen(["/usr/bin/gcc", "--print-prog-name", "cc1"], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	(o, e), x = p.communicate(), p.wait()

	return [re.sub(r'cc1$', r'include', o.strip())]

# Run cpp -Wp,-v and retrieve the search path from the stderr.
def getIncludePathFromCpp():
	p = subprocess.Popen(["/usr/bin/cpp", "-Wp,-v"], stdin = subprocess.PIPE, stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	(o, e), x = p.communicate(""), p.wait()

	lines = [x for x in map(lambda u: u.strip(), e.split("\n")) if len(x) > 0]
	print(lines)

	i0 = next(i for i, line in enumerate(lines) if "#include <...> search starts here:" == line)
	i1 = next(i for i, line in enumerate(lines) if "End of search list." == line)

	return lines[i0:i1]

def getAdditionalIncludePaths():
	# Make sure clang finds stdbool and stddef
	return getIncludePathFromCc1() + getIncludePathFromCpp()

def readInCode(fileList):
	code = ""
	for F in fileList:
		code += "\n" + open(F, "r").read() + "\n"

	# Remove unnecessary #includes
	for rx in [r'slurm/.*']:
		code = re.sub(re.compile(r'#include <%s>' % rx, re.MULTILINE), r'', code)

	return code

def parseCodeGetPpDefs(code):
	allPpDefs = []

	# Remove comments and strealine broken lines
	code = re.sub(re.compile(r'\\\s*\n'), '', \
		re.sub(re.compile(r'\/\*.*?\*\/', re.MULTILINE | re.DOTALL), '', code))

	rx = re.compile(r'#\s*define\s+([a-zA-Z_0-9]+)\s+([0-9a-fA-Fx\-]+)\s*\n')
	for name, value in rx.findall(code):
		if name in ["TRUE", "FALSE"]:	# CRAPPY_COMPILER is not defined
						# FIXME This is only necessary since we do not have a proper
						# parser
			continue

		allPpDefs += [dict(zip(["name", "value"], [name, value]))]

	return allPpDefs

def parseCodeGetDecls(code):
	allDecls = []

	def addOneDecl(allDecls, d):
		allDecls += [d]
		return True	# Means: Ok, continue ...

	callback = lambda d: addOneDecl(allDecls, d)

	toolArgs = ["-std=gnu11"]
	for d in getAdditionalIncludePaths():
		toolArgs += ["-I", d]

	# Please note: The .h suffix is important
	success = plugin.iterateAST(code, "slurm.h", toolArgs, callback)
	if not success:
		sys.stderr.write("plugin.iterateAST failed.\n")
		sys.exit(1)

	# throwAwayDecls = filter(lambda z: not z["isInMainFile"], allDecls)
	# for decl in throwAwayDecls:
	# 	print(decl)

	return filter(lambda z: z["isInMainFile"], allDecls)

def findTypedefForStruct(typedefDecls, structDecl):
	aliasList = []

	if "addressTypedefForAnonDecl" in structDecl.keys():
		aliasList += [next(u for u in typedefDecls if u["address"] == structDecl["addressTypedefForAnonDecl"])]

	for x in [u for u in typedefDecls if u["underlyingType"] == "struct %s" % structDecl["name"]]:
		if not x["name"] in [v["name"] for v in aliasList]:
			aliasList += [x]

	return aliasList

def extractStructs(allDecls):
	structDecls  = filter(lambda z:  "RecordDecl" == z["class"], allDecls)
	typedefDecls = filter(lambda z: "TypedefDecl" == z["class"], allDecls)

	structList = []
	for structDecl in structDecls:
		aliasList = findTypedefForStruct(typedefDecls, structDecl)

		if 0 == len(aliasList):
			structList += [{"name": structDecl["name"], "members": structDecl["fields"]}]
		else:
			for alias in aliasList:
				structList += [{"name": structDecl["name"], "members": structDecl["fields"], "typedef": alias["name"]}]

	return structList

def extractFunctions(allDecls):
	return [{"name": funcDecl["name"], "retVal": funcDecl["returnType"], "args": funcDecl["parameters"]} \
			for funcDecl in filter(lambda z:  "FunctionDecl" == z["class"], allDecls)]

if __name__ == "__main__":
	if len(sys.argv) < 3:
		sys.stderr.write("usage: script inFile inFile ... inFile outFile\n")
		sys.exit(1)

	outFile  = sys.argv[-1]
	fileList = sys.argv[1:-1]

	code     = readInCode(fileList)
	allDecls = parseCodeGetDecls(code)

	api = {"defines"  : parseCodeGetPpDefs(code), \
	       "structs"  : extractStructs(allDecls), \
	       "functions": extractFunctions(allDecls), \
	       "allDecls" : allDecls}

	with open(sys.argv[-1], "w") as f:
		f.write(json.dumps(api))

