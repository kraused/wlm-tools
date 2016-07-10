
import sys
import os
import re
import json


api = json.loads(open(sys.argv[1], "r").read())

f = open(sys.argv[2], "w")

f.write("""
#include <python2.7/Python.h>
#include <python2.7/structmember.h>

#include <slurm/slurm.h>

void slurm_verbose(const char *fmt, ...)
{
}

PyObject *slurmpyModule = NULL;

static void setSlurmpyErrno(int errorNum)
{
	PyObject *slurmpyErrno = PyLong_FromLong(errorNum);
	PyObject_SetAttrString(slurmpyModule, "errno", slurmpyErrno);
	Py_XDECREF(slurmpyErrno);
}

""")

#
# Type checking functions
#

def findStructRecordFromPtrType(tp):
	tp = re.sub(r'\s', r'', tp)

	for d in api["structs"]:
		if d["typedef"] == tp[:-1]:
			return d

	return None

def isPtrToKnownStruct(tp):
	return (None != findStructRecordFromPtrType(tp))

isString__rx1 = re.compile(r'char\s*\*$')
isString__rx2 = re.compile(r'const\s+char\s*\*$')
def isString(tp):
	return isString__rx1.match(tp) or isString__rx2.match(tp)

isSomeInt__rx1 = re.compile(r'[u]?int[0-9]+_t$')
def isSomeInt(tp):
	tp = re.sub(r'\s', r'', tp)

	# Not a complete list but good enough for us
	return (tp in ["int", "long", "time_t", "pid_t", "uid_t"]) or (tp in ["unsignedint", "unsignedlong"]) or isSomeInt__rx1.match(tp)

def isPtrToSomeInt(tp):
	tp = re.sub(r'\s', r'', tp)

	return ('*' == tp[-1]) and isSomeInt(tp[:-1])

def isPtrToString(tp):
	tp = re.sub(r'\s', r'', tp)

	return ('*' == tp[-1]) and isString(tp[:-1])

isVoidPtr__rx1 = re.compile(r'void\s*\*$')
def isVoidPtr(tp):
	return isVoidPtr__rx1.match(tp)

def isBool(tp):
	return ("bool" == tp)

# In support of pointers and arrays we need to create additional structures as wrappers
def figureOutAdditionalStructs(api):
	additionalStructs = []

	for d in api["structs"]:
	 	for x in d["members"]:
#			if isVoidPtr(x["type"]):
#				sys.stderr.write("Ignoring opaque pointer %s (%s)\n" % (str(x), d["typedef"]))
#				continue
			if isString(x["type"]) or isSomeInt(x["type"]) or isBool(x["type"]):
				continue

			if isPtrToKnownStruct(x["type"]):
				pass
#				additionalStructs += ["%s_PTR" % re.sub(r'\s', '', x["type"])[:-1]]
			elif isPtrToSomeInt(x["type"]):
				additionalStructs += [("integer", "%s" % re.sub(r'\s', '', x["type"])[:-1])]
			elif isPtrToString(x["type"]):
				additionalStructs += [("string", "char*")]
			elif isVoidPtr(x["type"]):
				additionalStructs += [("void", "void")]
			else:
				sys.stderr.write("How do I handle %s (%s)?\n" % (str(x), d["typedef"]))

	print(sorted(list(set(additionalStructs))))

	return sorted(list(set(additionalStructs)))

class PythonType:
	def __init__(self, name):
		self.name = name

		self.__ob_size = "0"
		self.__tp_name = "\"slurmpy.@\""
		self.__tp_basicsize = "sizeof(struct @_PyWrap)"
		self.__tp_itemsize = "0"
		self.__tp_dealloc = "NULL"
		self.__tp_print = "NULL"
		self.__tp_getattr = "NULL"
		self.__tp_setattr = "NULL"
		self.__tp_compare = "NULL"
		self.__tp_repr = "NULL"
		self.__tp_as_number = "NULL"
		self.__tp_as_sequence = "NULL"
		self.__tp_as_mapping = "NULL"
		self.__tp_hash = "NULL"
		self.__tp_call = "NULL"
		self.__tp_str = "NULL"
		self.__tp_getattro = "NULL"
		self.__tp_setattro = "NULL"
		self.__tp_as_buffer = "NULL"
		self.__tp_flags = "Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE"
		self.__tp_doc = "\"\""
		self.__tp_traverse = "NULL"
		self.__tp_clear = "NULL"
		self.__tp_richcompare = "NULL"
		self.__tp_weaklistoffset = "0"
		self.__tp_iter = "NULL"
		self.__tp_iternext = "NULL"
		self.__tp_methods = "@_PyWrap_methods"
		self.__tp_members = "@_PyWrap_members"
		self.__tp_getset = "NULL"
		self.__tp_base = "NULL"
		self.__tp_dict = "NULL"
		self.__tp_descr_get = "NULL"
		self.__tp_descr_set = "NULL"
		self.__tp_dictoffset = "0"
		self.__tp_init = "NULL"
		self.__tp_alloc = "NULL"
		self.__tp_new = "NULL"

		self.members = []
		self.deallocFunction = None
		self.newFunction     = None
		self.initFunction    = None
		self.getattrFunction = None
		self.setattrFunction = None
		self.getItemFunction = None
		self.setItemFunction = None

	def addMember(self, member):
		self.members += [member]

	def defineDeallocFunction(self, deallocBody):
		self.deallocFunction = """
static void @_PyWrap_dealloc(PyObject *obj)
{
	struct @_PyWrap *self __attribute__((unused));
	self = (struct @_PyWrap *)obj;
%s
	self->ob_type->tp_free(obj);
}
""" % deallocBody
		self.__tp_dealloc = "@_PyWrap_dealloc"

	def defineNewFunction(self, newBody):
		self.newFunction = """
static PyObject *@_PyWrap_new(PyTypeObject *type, PyObject *args, PyObject *kws)
{
        struct @_PyWrap *self;

        self = (struct @_PyWrap *)type->tp_alloc(type, 0);
        if (!self) {
                return NULL;
        }
%s
        return (PyObject *)self;
}
""" % newBody
		self.__tp_new = "@_PyWrap_new"

	def defineInitFunction(self, initBody):
		self.initFunction = """
static int @_PyWrap_init(PyObject *obj, PyObject *args, PyObject *kws)
{
	struct @_PyWrap *self __attribute__((unused));
	self = (struct @_PyWrap *)obj;
%s
        return 0;
}
""" % initBody
		self.__tp_init = "@_PyWrap_init"

	def defineGetattrFunction(self, getattrBody):
		self.getattrFunction = """
static PyObject *@_PyWrap_getattr(PyObject *obj, PyObject *name)
{
	struct @_PyWrap *self __attribute__((unused));
	self = (struct @_PyWrap *)obj;

	if (!PyString_Check(name)) {
		fprintf(stderr, "name is not a string.\\n");
		Py_RETURN_NONE;
	}
%s
	fprintf(stderr, "Unknown attribute \\"%%s\\" in %%s.\\n", PyString_AsString(name), __FUNCTION__);
	Py_RETURN_NONE;
}
""" % getattrBody
		self.__tp_getattro = "@_PyWrap_getattr"

	def defineSetattrFunction(self, setattrBody):
		self.setattrFunction = """
static int @_PyWrap_setattr(PyObject *obj, PyObject *name, PyObject *v)
{
	struct @_PyWrap *self __attribute__((unused));
	self = (struct @_PyWrap *)obj;
%s

	fprintf(stderr, "Unknown attribute \\"%%s\\" in %%s.\\n", PyString_AsString(name), __FUNCTION__);
	PyErr_SetString(PyExc_RuntimeError, "");
	return 1;
}
""" % setattrBody
		self.__tp_setattro = "@_PyWrap_setattr"

	def defineGetItemFunction(self, getItemBody):
		self.getItemFunction = """
static PyObject *@_PyWrap_getitem(PyObject *obj, PyObject *key)
{
	struct @_PyWrap *self __attribute__((unused));
	self = (struct @_PyWrap *)obj;
%s
	Py_RETURN_NONE;
}
""" % getItemBody

	def defineSetItemFunction(self, setItemBody):
		self.setItemFunction = """
static int @_PyWrap_setitem(PyObject *obj, PyObject *key, PyObject *v)
{
	struct @_PyWrap *self __attribute__((unused));
	self = (struct @_PyWrap *)obj;
%s
	fprintf(stderr, "%%s failure.\\n", __FUNCTION__);
	PyErr_SetString(PyExc_RuntimeError, "");
	return 1;
}
""" % setItemBody

	def declarations(self):
		o = """
struct @_PyWrap;
struct @_PyWrap *make_@();
"""

		if self.deallocFunction:
			o += "static void @_PyWrap_dealloc(PyObject *obj);\n"
		if self.newFunction:
			o += "static PyObject *@_PyWrap_new(PyTypeObject *type, PyObject *args, PyObject *kws);\n"
		if self.initFunction:
			o += "static int @_PyWrap_init(PyObject *obj, PyObject *args, PyObject *kws);\n"
		if self.getattrFunction:
			o += "static PyObject *@_PyWrap_getattr(PyObject *obj, PyObject *name);\n"
		if self.setattrFunction:
			o += "static int @_PyWrap_setattr(PyObject *obj, PyObject *name, PyObject *v);\n"
		if self.getItemFunction:
			o += "static PyObject *@_PyWrap_getitem(PyObject *obj, PyObject *key);\n"
		if self.setItemFunction:
			o += "static int @_PyWrap_setitem(PyObject *obj, PyObject *key, PyObject *v);\n"

		return re.sub(r'@', self.name, o)

	def definitions(self):
		o = """
struct @_PyWrap
{
	PyObject_HEAD
%s
};
""" % "\n".join(["\t%s %s;" % member for member in self.members])

		o += """
static PyMemberDef @_PyWrap_members[] =
{
	{NULL}
};

static PyMethodDef @_PyWrap_methods[] =
{
        {NULL}
};
"""

		if self.getItemFunction or self.setItemFunction:
			getItem = "NULL"
			if self.getItemFunction:
				getItem = "@_PyWrap_getitem"
			setItem = "NULL"
			if self.setItemFunction:
				setItem = "@_PyWrap_setitem"

			o += """
PyMappingMethods @_PyWrap_mapping =
{
	NULL,
	%s,
	%s
};
""" % (getItem, setItem)

			self.__tp_as_mapping = "&@_PyWrap_mapping"

		o += """
static PyTypeObject @_PyWrap_Type =
{
        PyObject_HEAD_INIT(NULL)
	%s
};
""" % (",\n\t".join([self.__ob_size, self.__tp_name, self.__tp_basicsize, self.__tp_itemsize, self.__tp_dealloc, self.__tp_print, self.__tp_getattr, self.__tp_setattr, self.__tp_compare, self.__tp_repr, self.__tp_as_number, self.__tp_as_sequence, self.__tp_as_mapping, self.__tp_hash, self.__tp_call, self.__tp_str, self.__tp_getattro, self.__tp_setattro, self.__tp_as_buffer, self.__tp_flags, self.__tp_doc, self.__tp_traverse, self.__tp_clear, self.__tp_richcompare, self.__tp_weaklistoffset, self.__tp_iter, self.__tp_iternext, self.__tp_methods, self.__tp_members, self.__tp_getset, self.__tp_base, self.__tp_dict, self.__tp_descr_get, self.__tp_descr_set, self.__tp_dictoffset, self.__tp_init, self.__tp_alloc, self.__tp_new]))

		return re.sub(r'@', self.name, o)

	def functions(self):
		o = ""

		self.makeFunction = """
struct @_PyWrap *make_@()
{
	PyObject *empty;
	struct @_PyWrap *self;

	empty = PyTuple_New(0);
	self  = (struct @_PyWrap *)PyObject_CallObject((PyObject *)&@_PyWrap_Type, empty);
	Py_XDECREF(empty);
	self->other = NULL;

	return self;
}
"""

		o += self.makeFunction

		if self.deallocFunction:
			o += self.deallocFunction
		if self.newFunction:
			o += self.newFunction
		if self.initFunction:
			o += self.initFunction
		if self.getattrFunction:
			o += self.getattrFunction
		if self.setattrFunction:
			o += self.setattrFunction
		if self.getItemFunction:
			o += self.getItemFunction
		if self.setItemFunction:
			o += self.setItemFunction

		return re.sub(r'@', self.name, o)

allWrapTypes = []
allWrapFunctions = []

additionalFunctions = ""

for cl, tp in figureOutAdditionalStructs(api):
	name = tp
	if "string" == cl:
		name = "string"

	T = PythonType("%s_PTR" % name)

	if "integer" == cl:
		T.addMember(("long ", "len"))

	T.addMember(("%s* " % tp, "objp"))
	T.addMember(("%s**" % tp, "objpp"))
	T.addMember(("PyObject*", "other"))

	deallocBody = """
	Py_XDECREF(self->other);
	self->other = NULL;

	if (self->objpp == &self->objp) {
"""
	if "integer" == cl:
		deallocBody += """
		free(self->objp);
		self->len   = 0;
"""
	if "string" == cl:
		deallocBody += """
		long i;

		for (i = 0; (NULL != self->objp[i]); ++i) {
			free(self->objp[i]);
		}
		free(self->objp);
"""

	deallocBody += """
		self->objp  = NULL;
		self->objpp = NULL;
	}
"""

	newBody = """
	self->other = NULL;
	self->objp  = NULL;
	self->objpp = NULL;
"""

	if "integer" == cl:
		newBody += """
	self->len = 0;
"""

	initBody = """
"""

	getItemBody = """
"""

	convertIndex = """
	long idx;

	if (!PyInt_Check(key)) {
		fprintf(stderr, "key is not an integer.\\n");
		Py_RETURN_NONE;
	}
	idx = PyInt_AsLong(key);
"""

	if "integer" == cl:
		getItemBody = convertIndex + """
	long val = (*self->objpp)[idx];

	return PyInt_FromLong(val);
"""
	if "string" == cl:
		getItemBody = convertIndex + """
	char *val = *((*self->objpp) + idx);

	if (!val) {
		Py_RETURN_NONE;
	} else {
		return PyString_FromString(val);
	}
"""

	setItemBody = """
"""

	T.defineNewFunction(newBody)
	T.defineInitFunction(initBody)
	T.defineDeallocFunction(deallocBody)
	T.defineGetItemFunction(getItemBody)
	T.defineSetItemFunction(setItemBody)

	allWrapTypes += [T]

	additionalFunctions += """
static PyObject *convert_list_to_%s_PyWrap(PyObject *obj, PyObject *args)
{
	struct %s_PyWrap *self __attribute__((unused));

	PyObject *list;
	PyObject *item;
	long i, n;

	if (!PyArg_ParseTuple(args, "O", &list)) {
		Py_RETURN_NONE;
	}

	n = PyList_Size(list);

	self = make_%s();
	self->objp  = malloc(n*sizeof(%s));
	self->objpp = &self->objp;

	for (i = 0; i < n; ++i) {
		item = PyList_GetItem(list, i);
		if (!item) {
			Py_XDECREF(self);
			Py_RETURN_NONE;
		}
""" % (tuple(["%s_PTR" % name]*3) + (tp,)) # + tuple(["%s_PTR" % name]*1))

	if "string" == cl:
		additionalFunctions += """
		if (Py_None == item) {
			self->objp[i] = NULL;
		} else if (PyString_Check(item)) {
			self->objp[i] = strdup(PyString_AsString(item));
		} else {
			PyErr_SetString(PyExc_RuntimeError, "Invalid argument");

			Py_XDECREF(self);
			Py_RETURN_NONE;
		}
"""
	if "integer" == cl:
		additionalFunctions += """
		if (PyString_Check(item)) {
			self->objp[i] = PyInt_AsLong(item);
		} else {
			PyErr_SetString(PyExc_RuntimeError, "Invalid argument");

			Py_XDECREF(self);
			Py_RETURN_NONE;
		}
"""

	additionalFunctions += """
	}
"""

	if "integer" == cl:
		additionalFunctions += """
	self->len = n;
"""

	additionalFunctions += """
	return (PyObject *)self;
}
"""

	allWrapFunctions += [("convert_list_to_%s_PTR" % name, "convert_list_to_%s_PTR_PyWrap" % name, "Convert a list to a %s_PTR instance" % name)]

for d in api["structs"]:
	assert(len(d["typedef"]) > 0)	# We use the typedef rather than the name since
					# the current slurm.h contains at least one anonymous
					# structure.

	if 1:
		T = PythonType("%s_PTR" % d["typedef"])

		T.addMember(("%s* " % d["typedef"], "objp"))
		T.addMember(("%s**" % d["typedef"], "objpp"))
		T.addMember(("PyObject*", "other"))
		T.addMember(("void (*freeCb)(%s*)" % d["typedef"], ""))

		deallocBody = """
	Py_XDECREF(self->other);
	self->other = NULL;

	if (self->objpp == &self->objp) {
		if (self->freeCb) {
			self->freeCb(self->objp);
			self->objp  = NULL;
			self->objpp = NULL;
		} else {
			fprintf(stderr, "No dealloc callback defined for @_PyWrap. The code leaks memory!\\n");
		}
	}
"""

		newBody = """
	self->other  = NULL;
	self->objp   = NULL;
	self->objpp  = NULL;
	self->freeCb = NULL;
"""

		initBody = """
"""

		getattrBody = """
"""

		setattrBody = """
"""
		getItemBody = """
"""

		if len(d["members"]) > 0:
			getItemBody = """
	long idx;
	struct %s_PyWrap *item;

	if (!PyInt_Check(key)) {
		fprintf(stderr, "key is not an integer.\\n");
		Py_RETURN_NONE;
	}
	idx = PyInt_AsLong(key);

	item = make_%s();

	if (NULL == (*self->objpp)) {
		fprintf(stderr, "*self->objpp is NULL in %%s\\n", __FUNCTION__);
		Py_RETURN_NONE;
	}

	item->objp  = (*self->objpp) + idx;

	item->other = (PyObject *)self;
	Py_XINCREF(self);

	return (PyObject *)item;
""" % tuple([d["typedef"]]*2)

		setItemBody = """
"""

		T.defineNewFunction(newBody)
		T.defineInitFunction(initBody)
		T.defineDeallocFunction(deallocBody)
		T.defineGetattrFunction(getattrBody)
		T.defineSetattrFunction(setattrBody)
		T.defineGetItemFunction(getItemBody)
		T.defineSetItemFunction(setItemBody)

		allWrapTypes += [T]

	if len(d["members"]) > 0:
		T = PythonType("%s" % d["typedef"])

		T.addMember(("%s " % d["typedef"], "obj"))
		T.addMember(("%s*" % d["typedef"], "objp"))
		T.addMember(("PyObject*", "other"))

		deallocBody = """
	Py_XDECREF(self->other);
	self->other = NULL;

	/* If objp points to obj we need to deallocate. Otherwise obj is just trash.
	 */
	if (self->objp == &self->obj) {
"""

		for x in d["members"]:
			if isString(x["type"]):
				deallocBody += """
	if (self->obj.%s) {
		free(self->obj.%s);
	}
""" % tuple([x["name"]]*2)
			elif isSomeInt(x["type"]) or isBool(x["type"]):
				pass
			elif isPtrToKnownStruct(x["type"]):
				sys.stderr.write("How to dealloc %s?\n" % str(x))
				deallocBody += """
		if (self->obj.%s) {
			fprintf(stderr, "No dealloc routine defined for @_PyWrap:%s member (type %s). The code leaks memory!\\n");
		}
""" % (tuple([x["name"]]*2) + (x["type"],))
			elif isPtrToSomeInt(x["type"]):
				deallocBody += """
	if (self->obj.%s) {
		free(self->obj.%s);
	}
""" % tuple([x["name"]]*2)
			elif isPtrToString(x["type"]):
				deallocBody += """
{
	long i;

	if (self->obj.%s) {
		for (i = 0; self->obj.%s[i]; ++i) {
			free(self->obj.%s[i]);
		}
		free(self->obj.%s);
	}
}
""" % tuple([x["name"]]*4)
			else:
				sys.stderr.write("How to handle %s?\n" % str(x))

		deallocBody += """
	}
"""

		newBody = """
	self->other = NULL;

	memset(&self->obj, 0, sizeof(self->obj));
	self->objp  = &self->obj;
"""

		initBody = """
"""

		getattrBody = """
"""

		setattrBody = """
"""

		commonIf = """\tif (!strcmp("%s", PyString_AsString(name))) """

		for x in d["members"]:
			if isString(x["type"]):
				getattrBody += (commonIf % x["name"]) + """{
	if (self->objp->%s) {
		return PyString_FromString(self->objp->%s);
	} else {
		Py_RETURN_NONE;
	}
}""" % tuple([x["name"]]*2)
				setattrBody += (commonIf % x["name"]) + """{
	if (self->objp->%s) {
		free(self->objp->%s);
	}

	if (Py_None == v) {
		self->objp->%s = NULL;
		return 0;
	}
	else if (PyString_Check(v)) {
		self->objp->%s = strdup(PyString_AsString(v));
		return 0;
	} else {
		PyErr_SetString(PyExc_RuntimeError, "Invalid argument");
		return 1;
	}
}""" % tuple([x["name"]]*4)
			elif isSomeInt(x["type"]):
				getattrBody += (commonIf % x["name"]) + """{
	return PyInt_FromLong(self->objp->%s);
}""" % x["name"]
				setattrBody += (commonIf % x["name"]) + """{
	if (!PyInt_Check(v)) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid argument");
		return 1;
	}

	self->objp->%s = PyInt_AsLong(v);
	return 0;
}""" % x["name"]
			elif isBool(x["type"]):
				getattrBody += (commonIf % x["name"]) + """{
	return PyBool_FromLong(self->objp->%s);
}""" % x["name"]
				setattrBody += (commonIf % x["name"]) + """{

	if (!PyBool_Check(v)) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid argument");
		return 1;
	}

	if (Py_False == v) {
		self->objp->%s = 0;
		return 0;
	}
	if (Py_True  == v) {
		self->objp->%s = 1;
		return 0;
	}
}""" % tuple([x["name"]]*2)
			elif isPtrToKnownStruct(x["type"]):
				d = findStructRecordFromPtrType(x["type"])
				if 0 == len(d["members"]):
					continue

				getattrBody += (commonIf % x["name"]) + """{
	struct %s_PTR_PyWrap *val;

	val = make_%s_PTR();
	val->objpp = &self->objp->%s;

	val->other = (PyObject *)self;
	Py_XINCREF(self);

	return (PyObject *)val;
}""" % (tuple([re.sub(r'\s', '', x["type"])[:-1]]*2) + (x["name"],))
				setattrBody += (commonIf % x["name"]) + """{
	PyErr_SetString(PyExc_NotImplementedError, "");
	return 1;
}"""
			elif isPtrToSomeInt(x["type"]):
				getattrBody += (commonIf % x["name"]) + """{
	struct %s_PTR_PyWrap *val;

	val = make_%s_PTR();
	val->objpp = &self->objp->%s;

	val->other = (PyObject *)self;
	Py_XINCREF(self);

	return (PyObject *)val;
}""" % (tuple([re.sub(r'\s', '', x["type"])[:-1]]*2) + (x["name"],))
				setattrBody += (commonIf % x["name"]) + """{
	long i;
	struct %s_PTR_PyWrap *val;

	if (!PyObject_IsInstance(v, (PyObject *)&%s_PTR_PyWrap_Type)) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid argument");
		return 1;
	}
	val = (struct %s_PTR_PyWrap *)v;

	if (self->objp->%s) {
		free(self->objp->%s);
	}

	self->objp->%s = malloc(val->len*sizeof(%s));
	for (i = 0; val->len; ++i) {
		self->objp->%s[i] = (*val->objpp)[i];
	}

	return 0;
}""" % (tuple([re.sub(r'\s', '', x["type"])[:-1]]*3) + tuple([x["name"]]*3) + tuple([re.sub(r'\s', '', x["type"])[:-1]]*1) + tuple([x["name"]]*1))
			elif isPtrToString(x["type"]):
				getattrBody += (commonIf % x["name"]) + """{
	struct string_PTR_PyWrap *val;

	val = make_string_PTR();
	val->objpp = &self->objp->%s;

	val->other = (PyObject *)self;
	Py_XINCREF(self);

	return (PyObject *)val;
}""" % (x["name"],)
				setattrBody += (commonIf % x["name"]) + """{
	long i, n;
	struct string_PTR_PyWrap *val;

	if (!PyObject_IsInstance(v, (PyObject *)&string_PTR_PyWrap_Type)) {
		PyErr_SetString(PyExc_RuntimeError, "Invalid argument");
		return 1;
	}
	val = (struct string_PTR_PyWrap *)v;

	for (n = 0; (*val->objpp)[n]; ++n);
	++n;

	if (self->objp->%s) {
		for (i = 0; self->objp->%s[i]; ++i)
			free(self->objp->%s[i]);
		free(self->objp->%s);
	}

	self->objp->%s = malloc(n*sizeof(char*));
	for (i = 0;; ++i) {
		if ((*val->objpp)[i]) {
			self->objp->%s[i] = strdup((*val->objpp)[i]);
		} else {
			self->objp->%s[i] = NULL;
			break;
		}
	}

	return 0;
}""" % tuple([x["name"]]*7)
			elif isVoidPtr(x["type"]):
				getattrBody += (commonIf % x["name"]) + """{
	struct %s_PTR_PyWrap *val;

	val = make_%s_PTR();
	val->objpp = &self->objp->%s;

	val->other = (PyObject *)self;
	Py_XINCREF(self);

	return (PyObject *)val;
}""" % (tuple([re.sub(r'\s', '', x["type"])[:-1]]*2) + (x["name"],))
				setattrBody += (commonIf % x["name"]) + """{
	PyErr_SetString(PyExc_NotImplementedError, "");
	return 1;
}"""
			else:
				sys.stderr.write("How to handle %s?\n" % str(x))

		T.defineNewFunction(newBody)
		T.defineInitFunction(initBody)
		T.defineDeallocFunction(deallocBody)
		T.defineGetattrFunction(getattrBody)
		T.defineSetattrFunction(setattrBody)

		allWrapTypes += [T]

for T in allWrapTypes:
	f.write(T.declarations())
for T in allWrapTypes:
	f.write(T.definitions())
for T in allWrapTypes:
	f.write(T.functions())

f.write(additionalFunctions)

functionBlacklist = [re.compile(r'slurm_list_.*', 0), re.compile(r'slurm_hostlist_.*', 0), re.compile(r'slurm_update_block', 0), re.compile(r'slurm_allocation_msg_thr_create', 0), re.compile(r'slurm_allocation_msg_thr_destroy', 0), re.compile(r'slurm_step_ctx_create', 0), re.compile(r'slurm_step_ctx_get', 0), re.compile(r'slurm_jobinfo_ctx_get', 0), re.compile(r'slurm_step_ctx_daemon_per_node_hack', 0), re.compile(r'slurm_step_ctx_destroy', 0), re.compile(r'slurm_step_launch', 0), re.compile(r'slurm_step_launch_add', 0), re.compile(r'slurm_step_launch_wait_start', 0), re.compile(r'slurm_step_launch_wait_finish', 0), re.compile(r'slurm_step_launch_abort', 0), re.compile(r'slurm_step_launch_fwd_signal', 0), re.compile(r'slurm_step_launch_fwd_wake', 0), re.compile(r'slurm_job_cpus_allocated_on_node_id', 0), re.compile(r'slurm_job_cpus_allocated_on_node', 0), re.compile(r'slurm_get_end_time', 0), re.compile(r'slurm_pid2jobid', 0), re.compile(r'slurm_job_step_pids_response_msg_free', 0), re.compile(r'slurm_get_select_jobinfo', 0), re.compile(r'slurm_get_select_nodeinfo', 0), re.compile(r'slurm_init_part_desc_msg', 0), re.compile(r'slurm_create_partition', 0), re.compile(r'slurm_update_partition', 0), re.compile(r'slurm_checkpoint_able', 0), re.compile(r'slurm_checkpoint_error', 0)]

for d in api["functions"]:
	skip = False
	for rx in functionBlacklist:
		if rx.match(d["name"]):
			skip = True
	if skip:
		continue

	allWrapFunctions += [(d["name"], "%s_PyWrap" % d["name"], "Wrapper around %s" % d["name"])]

	f.write("""\
static PyObject *%s_PyWrap(PyObject *self, PyObject *args)
{
""" % d["name"])

	f.write("""\t/* %s %s(%s); */\n""" % (d["retVal"], d["name"], ", ".join(["%s %s" % (x["type"], x["name"]) for x in d["args"]])))

	if isSomeInt(d["retVal"]):
		f.write("""\
	long long retVal = 1;
""")
	if isString(d["retVal"]):
		f.write("""\
	char *retVal = NULL;
""")

	isPointerPointer = lambda a: re.match(r'.*\*\s*\*$', a["type"])
	isPointer        = lambda a: re.match(r'.*\*$', a["type"])

	for i, a in enumerate(d["args"]):
		if '?' == a["type"]:	# No support for variable argument calls yet
			continue

		name = a["name"]
		if '' == name:
			name = "arg%02d" % i

		if isPointerPointer(a):
			f.write("""\tstruct %s_PTR_PyWrap *a_%s = NULL;\n""" % (re.sub(r'\s', '', a["type"])[:-2], name))
		elif isPointer(a):
			if isString(a["type"]):
				f.write("""\tchar *a_%s;\n""" % (name,))
				f.write("""\tPyObject *dummy_%s;\n""" % name)
			elif isPtrToKnownStruct(a["type"]):
				f.write("""\tstruct %s_PyWrap *a_%s;\n""" % (re.sub(r'\s', '', a["type"])[:-1], name))
			elif re.match(r'FILE\s*\*', a["type"]):
				f.write("""\tFILE *a_%s;\n""" % (name,))
				f.write("""\tPyObject *dummy_%s;\n""" % name)
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))
		else:
			f.write("""\t%s a_%s;\n""" % (a["type"], name))
			if isSomeInt(a["type"]) or a["type"] in ['time_t', 'bool', 'uid_t']:
				f.write("""\tlong long dummy_%s;\n""" % name)
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))

	xxx = []
	zzz = []
	for i, a in enumerate(d["args"]):
		if '?' == a["type"]:	# No support for variable argument calls yet
			continue

		name = a["name"]
		if '' == name:
			name = "arg%02d" % i

		if isPointerPointer(a):
			xxx += ["O"]
			zzz += ["(PyObject *)&a_%s" % name]	# FIXME Totally unsafe!!!
			pass
		elif isPointer(a):
			if isString(a["type"]):
				xxx += ["S"]
				zzz += ["&dummy_%s" % name]
			elif isPtrToKnownStruct(a["type"]):
				xxx += ["O"]
				zzz += ["(PyObject *)&a_%s" % name]
			elif re.match(r'FILE\s*\*', a["type"]):
				xxx += ["O"]
				zzz += ["&dummy_%s" % name]
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))
		else:
			if isSomeInt(a["type"]) or a["type"] in ['time_t', 'bool', 'uid_t']:
				xxx += ["L"]
				zzz += ["&dummy_%s" % name]
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))

	if len(xxx) > 0:
		f.write("""
	if (!PyArg_ParseTuple(args, "%s", %s)) {
		Py_RETURN_NONE;
	}

""" % ("".join(xxx), ", ".join(zzz)))

	for i, a in enumerate(d["args"]):
		if '?' == a["type"]:	# No support for variable argument calls yet
			continue

		name = a["name"]
		if '' == name:
			name = "arg%02d" % i

		if isPointerPointer(a):
			f.write("""\ta_%s->objpp = &a_%s->objp;\n""" % (name, name))

			# Try to figure out if we have a free function in the API
			q = re.sub(r'_t.*', '', a["type"])
			for z in api["functions"]:
				# Manual fix for a stupid naming mistake in the API.
				if ("submit_response_msg" == q and "slurm_free_submit_response_response_msg" == z["name"]) or \
				   re.match(r'.*free_%s.*' % q, z["name"]) or \
				   re.match(r'.*%s_free.*' % q, z["name"]):
					f.write("""\ta_%s->freeCb = %s;\n""" % (name, z["name"]))
					break
		elif isPointer(a):
			if isString(a["type"]):
				f.write("""\ta_%s = PyString_AsString(dummy_%s);\n""" % (name, name))
			elif isPtrToKnownStruct(a["type"]):
				pass
			elif re.match(r'FILE\s*\*', a["type"]):
				f.write("""\
	if (!PyFile_Check((PyObject *)dummy_%s)) {
		fprintf(stderr, "Argument is not a file.\\n");
		Py_RETURN_NONE;
	}

	a_%s = PyFile_AsFile(dummy_%s);
	PyFile_IncUseCount((PyFileObject *)dummy_%s);
""" % tuple([name]*4))
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))
		else:
			if isSomeInt(a["type"]) or a["type"] in ['time_t', 'bool', 'uid_t']:
				f.write("""\ta_%s = dummy_%s;\n""" % (name, name))
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))

	xxx = "\t"
	if "void" == d["retVal"]:
		pass
	elif isSomeInt(d["retVal"]) or isString(d["retVal"]):
		xxx += "retVal = "
	else:
		sys.stderr.write("Return value %s is not handled properly.\n" % d["retVal"])

	zzz = []
	for i, a in enumerate(d["args"]):
		if '?' == a["type"]:	# No support for variable argument calls yet
			continue

		name = a["name"]
		if '' == name:
			name = "arg%02d" % i

		if isPointerPointer(a):
			zzz += ["&a_%s->objp" % name]
		else:
			if isPtrToKnownStruct(a["type"]):
				zzz += ["a_%s->objp" % name]
			else:
				zzz += ["a_%s" % name]

	f.write("""errno = 0;\n""")
	f.write("%s%s(%s);\n" % (xxx, d["name"], ", ".join(zzz)))
	f.write("""
	setSlurmpyErrno(errno);
""")

	for i, a in enumerate(d["args"]):
		if '?' == a["type"]:	# No support for variable argument calls yet
			continue

		name = a["name"]
		if '' == name:
			name = "arg%02d" % i

		if isPointerPointer(a):
			pass
		elif isPointer(a):
			if isString(a["type"]):
				pass
			elif isPtrToKnownStruct(a["type"]):
				pass
			elif re.match(r'FILE\s*\*', a["type"]):
				f.write("""
	PyFile_DecUseCount((PyFileObject *)dummy_%s);
""" % tuple([name]*1))
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))
		else:
			if isSomeInt(a["type"]) or a["type"] in ['time_t', 'bool', 'uid_t']:
				pass
			else:
				sys.stderr.write("How do I handle argument %s?\n" % str(a))

	if "void" == d["retVal"]:
		f.write("""
	Py_RETURN_NONE;
""")
	elif isSomeInt(d["retVal"]):
		f.write("""
	return Py_BuildValue("L", retVal);
""")
	elif isString(d["retVal"]):
		f.write("""
	return Py_BuildValue("s", retVal);
""")
	else:
		sys.stderr.write("Return value %s is not handled properly.\n" % d["retVal"])
		f.write("""
	Py_RETURN_NONE;
""")

	f.write("""\
}
""")

f.write("""
static PyMethodDef methods[] =
{
""")

for name, wrap, comment in allWrapFunctions:
	f.write("\t{\"%s\", %s, METH_VARARGS, \"Wrapper around %s\"},\n" % (name, wrap, comment))

f.write("""\
	{NULL, NULL, 0, NULL}
};
""")

f.write("""
PyMODINIT_FUNC initslurmpy()
{
	slurmpyModule = Py_InitModule("slurmpy", methods);
""")

f.write("\n\t/* structs */\n")
for T in allWrapTypes:
	f.write("""
	if (PyType_Ready(&%s) < 0) {
		fprintf(stderr, "PyType_Ready() failed for %s.\\n");
	} else {
		Py_INCREF(&%s);
		PyModule_AddObject(slurmpyModule, "%s", (PyObject *)&%s);
	}
""" % (tuple([T.name + "_PyWrap_Type"]*3) + (T.name,) + tuple([T.name + "_PyWrap_Type"]*1)))

f.write("\n\t/* enums */\n")
for d in api["enums"]:
	for x in d["members"]:
		f.write("\tPyModule_AddIntConstant(slurmpyModule, \"%s\", %s); /* %s */\n" % (tuple([x]*2) + (d["name"],)))
f.write("\n\t/* pp defines */\n")
for d in api["defines"]:
	f.write("\tPyModule_AddIntConstant(slurmpyModule, \"%s\", %s);\n" % tuple([d["name"]]*2))

f.write("""
	setSlurmpyErrno(0);
""")

f.write("""}
""")

