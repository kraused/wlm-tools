
import sys
import os
import re
import json
import subprocess

import plugin

def getAdditionalIncludePaths():
	# Make sure clang finds stdbool and stddef
	p = subprocess.Popen(["/usr/bin/gcc", "--print-prog-name", "cc1"], stdout = subprocess.PIPE, stderr = subprocess.PIPE)
	(o, e), x = p.communicate(), p.wait()

	return [re.sub(r'cc1$', r'include', o.strip())]

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

def extractEnums(allDecls):
	return [{"name": enumDecl["name"], "members": [x["name"] for x in enumDecl["enumerators"]]} \
			for enumDecl in filter(lambda z: "EnumDecl" == z["class"], allDecls)]

def findTypedefForStruct(typedefDecls, structDecl):
	alias = None

	if "addressTypedefForAnonDecl" in structDecl.keys():
		alias = next(u for u in typedefDecls if u["address"] == structDecl["addressTypedefForAnonDecl"])
	else:
		tmp = [u for u in typedefDecls if u["underlyingType"] == "struct %s" % structDecl["name"]]
		if 1 == len(tmp):
			alias = tmp[0]

	return alias

def extractStructs(allDecls):
	structDecls  = filter(lambda z:  "RecordDecl" == z["class"], allDecls)
	typedefDecls = filter(lambda z: "TypedefDecl" == z["class"], allDecls)

	structList = []
	for structDecl in structDecls:
		d = {"name": structDecl["name"], "members": structDecl["fields"]}

		alias = findTypedefForStruct(typedefDecls, structDecl)
		if alias:
			d["typedef"] = alias["name"]

		structList += [d]

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

	api = {"enums"    : extractEnums(allDecls), \
	       "defines"  : parseCodeGetPpDefs(code), \
	       "structs"  : extractStructs(allDecls), \
	       "functions": extractFunctions(allDecls)}

	with open(sys.argv[-1], "w") as f:
		f.write(json.dumps(api))

