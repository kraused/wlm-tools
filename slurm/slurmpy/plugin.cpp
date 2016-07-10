
#include <python2.7/Python.h>

#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>

#include "clang/AST/ASTConsumer.h"
#include "clang/AST/RecursiveASTVisitor.h"
#include "clang/Frontend/CompilerInstance.h"
#include "clang/Frontend/FrontendAction.h"
#include "clang/Tooling/Tooling.h"

#include "common.h"

class PluginVisitor : public clang::RecursiveASTVisitor<PluginVisitor>
{

public:
	explicit					PluginVisitor(clang::ASTContext *context, PyObject *callback);

public:
	bool						VisitDecl(clang::Decl *decl);

private:
	clang::ASTContext				*_context;

private:
	PyObject					*_callback;

};

class PluginConsumer : public clang::ASTConsumer
{

public:
	explicit					PluginConsumer(clang::ASTContext *context, PyObject *callback);

public:
	virtual void					HandleTranslationUnit(clang::ASTContext &context);

private:
	PluginVisitor					_visitor;

};

class PluginAction : public clang::ASTFrontendAction
{

public:
	explicit					PluginAction(PyObject *callback);

public:
	virtual std::unique_ptr<clang::ASTConsumer>	CreateASTConsumer(clang::CompilerInstance &compiler, llvm::StringRef inFile);

private:
	PyObject					*_callback;

};

PluginVisitor::PluginVisitor(clang::ASTContext *context, PyObject *callback)
: _context(context), _callback(callback)
{
}

bool PluginVisitor::VisitDecl(clang::Decl *decl)
{
	PyObject *d;
	PyObject *x;
	PyObject *f;
	PyObject *l;
	SInt32 err;

	if (!(clang::FunctionDecl::classof(decl) ||
	      clang::RecordDecl::classof(decl) ||
	      clang::EnumDecl::classof(decl) ||
	      clang::TypedefDecl::classof(decl))) {
		return true;
	}

	d = PyDict_New();
	if (UNLIKELY(!d)) {
		/* FIXME: Raise exception from here? */
		return false;
	}

#define SET_PYDICT_ITEM(D, KEY, VAL)					\
	do {								\
		err = PyDict_SetItem(D, KEY, VAL);			\
		if (UNLIKELY(err)) {					\
			/* FIXME: Raise exception from here? */		\
		}							\
	} while(0)

	if (clang::FunctionDecl::classof(decl)) {
		clang::FunctionDecl *funcDecl = (clang::FunctionDecl *)decl;

		SET_PYDICT_ITEM(d, PyString_FromString("class"), PyString_FromString("FunctionDecl"));
		SET_PYDICT_ITEM(d, PyString_FromString("name") , PyString_FromString(funcDecl->getName().str().c_str()));
		SET_PYDICT_ITEM(d, PyString_FromString("filename"), PyString_FromString(_context->getSourceManager().getPresumedLoc(funcDecl->getLocStart()).getFilename()));
		SET_PYDICT_ITEM(d, PyString_FromString("line"), PyInt_FromLong(_context->getSourceManager().getPresumedLoc(funcDecl->getLocStart()).getLine()));
		SET_PYDICT_ITEM(d, PyString_FromString("isInMainFile"), PyBool_FromLong(_context->getSourceManager().isInMainFile(funcDecl->getLocStart())));
		SET_PYDICT_ITEM(d, PyString_FromString("address"), PyString_FromFormat("%p", funcDecl));

		SET_PYDICT_ITEM(d, PyString_FromString("returnType"), PyString_FromString(funcDecl->getReturnType().getAsString().c_str()));

		l = PyList_New(0);
		if (UNLIKELY(!d)) {
			/* FIXME: Raise exception from here? */
			return false;
		}

		for (const auto *x: funcDecl->parameters()) {
			f = PyDict_New();
			if (UNLIKELY(!f)) {
				/* FIXME: Raise exception from here? */
				return false;
			}

			SET_PYDICT_ITEM(f, PyString_FromString("name"), PyString_FromString(x->getName().str().c_str()));
			SET_PYDICT_ITEM(f, PyString_FromString("type"), PyString_FromString(x->getType().getAsString().c_str()));

			PyList_Append(l, f);
		}

		SET_PYDICT_ITEM(d, PyString_FromString("parameters"), l);
	}
	if (clang::RecordDecl::classof(decl)) {
		clang::RecordDecl *structDecl = (clang::RecordDecl *)decl;

		SET_PYDICT_ITEM(d, PyString_FromString("class"), PyString_FromString("RecordDecl"));
		SET_PYDICT_ITEM(d, PyString_FromString("name") , PyString_FromString(structDecl->getName().str().c_str()));
		SET_PYDICT_ITEM(d, PyString_FromString("filename"), PyString_FromString(_context->getSourceManager().getPresumedLoc(structDecl->getLocStart()).getFilename()));
		SET_PYDICT_ITEM(d, PyString_FromString("line"), PyInt_FromLong(_context->getSourceManager().getPresumedLoc(structDecl->getLocStart()).getLine()));
		SET_PYDICT_ITEM(d, PyString_FromString("isInMainFile"), PyBool_FromLong(_context->getSourceManager().isInMainFile(structDecl->getLocStart())));
		SET_PYDICT_ITEM(d, PyString_FromString("address"), PyString_FromFormat("%p", structDecl));

		SET_PYDICT_ITEM(d, PyString_FromString("isAnonymous"), PyBool_FromLong(structDecl->isAnonymousStructOrUnion()));

		if (structDecl->getTypedefNameForAnonDecl()) {
			SET_PYDICT_ITEM(d, PyString_FromString("addressTypedefForAnonDecl"), PyString_FromFormat("%p", structDecl->getTypedefNameForAnonDecl()));
	}

		l = PyList_New(0);
		if (UNLIKELY(!d)) {
			/* FIXME: Raise exception from here? */
			return false;
		}

		for (const auto *x : structDecl->fields()) {
			f = PyDict_New();
			if (UNLIKELY(!f)) {
				/* FIXME: Raise exception from here? */
				return false;
			}

			SET_PYDICT_ITEM(f, PyString_FromString("name"), PyString_FromString(x->getName().str().c_str()));
			SET_PYDICT_ITEM(f, PyString_FromString("type"), PyString_FromString(x->getType().getAsString().c_str()));

			PyList_Append(l, f);
		}

		SET_PYDICT_ITEM(d, PyString_FromString("fields"), l);
	}
	if (clang::EnumDecl::classof(decl)) {
		clang::EnumDecl *enumDecl = (clang::EnumDecl *)decl;

		SET_PYDICT_ITEM(d, PyString_FromString("class"), PyString_FromString("EnumDecl"));
		SET_PYDICT_ITEM(d, PyString_FromString("name") , PyString_FromString(enumDecl->getName().str().c_str()));
		SET_PYDICT_ITEM(d, PyString_FromString("filename"), PyString_FromString(_context->getSourceManager().getPresumedLoc(enumDecl->getLocStart()).getFilename()));
		SET_PYDICT_ITEM(d, PyString_FromString("line"), PyInt_FromLong(_context->getSourceManager().getPresumedLoc(enumDecl->getLocStart()).getLine()));
		SET_PYDICT_ITEM(d, PyString_FromString("isInMainFile"), PyBool_FromLong(_context->getSourceManager().isInMainFile(enumDecl->getLocStart())));
		SET_PYDICT_ITEM(d, PyString_FromString("address"), PyString_FromFormat("%p", enumDecl));

		l = PyList_New(0);
		if (UNLIKELY(!d)) {
			/* FIXME: Raise exception from here? */
			return false;
		}

		for (const auto *x : enumDecl->enumerators()) {
			if (!clang::EnumConstantDecl::classof(x)) {
				printf("?\n");
			}

			f = PyDict_New();
			if (UNLIKELY(!f)) {
				/* FIXME: Raise exception from here? */
				return false;
			}

			SET_PYDICT_ITEM(f, PyString_FromString("name"), PyString_FromString(x->getName().str().c_str()));
			SET_PYDICT_ITEM(f, PyString_FromString("type"), PyString_FromString(x->getType().getAsString().c_str()));

			PyList_Append(l, f);
		}

		SET_PYDICT_ITEM(d, PyString_FromString("enumerators"), l);
	}
	if (clang::TypedefDecl::classof(decl)) {
		clang::TypedefDecl *typedefDecl = (clang::TypedefDecl *)decl;

		SET_PYDICT_ITEM(d, PyString_FromString("class"), PyString_FromString("TypedefDecl"));
		SET_PYDICT_ITEM(d, PyString_FromString("name") , PyString_FromString(typedefDecl->getName().str().c_str()));
		SET_PYDICT_ITEM(d, PyString_FromString("filename"), PyString_FromString(_context->getSourceManager().getPresumedLoc(typedefDecl->getLocStart()).getFilename()));
		SET_PYDICT_ITEM(d, PyString_FromString("line"), PyInt_FromLong(_context->getSourceManager().getPresumedLoc(typedefDecl->getLocStart()).getLine()));
		SET_PYDICT_ITEM(d, PyString_FromString("isInMainFile"), PyBool_FromLong(_context->getSourceManager().isInMainFile(typedefDecl->getLocStart())));
		SET_PYDICT_ITEM(d, PyString_FromString("address"), PyString_FromFormat("%p", typedefDecl));

		SET_PYDICT_ITEM(d, PyString_FromString("underlyingType"), PyString_FromString(typedefDecl->getUnderlyingType().getAsString().c_str()));
	}

	x = PyObject_Call(_callback, Py_BuildValue("(O)", d), NULL);

	if (!PyBool_Check(x)) {
		/* FIXME Error */
	}

	return ((Py_True == x) ? true : false);
}

PluginConsumer::PluginConsumer(clang::ASTContext *context, PyObject *callback)
: _visitor(context, callback)
{
}

void PluginConsumer::HandleTranslationUnit(clang::ASTContext &context)
{
	_visitor.TraverseDecl(context.getTranslationUnitDecl());
}

PluginAction::PluginAction(PyObject *callback)
: _callback(callback)
{
}

std::unique_ptr<clang::ASTConsumer> PluginAction::CreateASTConsumer(clang::CompilerInstance &compiler, llvm::StringRef inFile)
{
	return std::unique_ptr<clang::ASTConsumer>(new PluginConsumer(&compiler.getASTContext(), _callback));
}

static PyObject* iterateAST(PyObject *self, PyObject *args)
{
	const char *code;
	const char *name;
	PyObject *toolArgsList;
	PyObject *callback;
	SInt64 i;
	PyObject *x;
	bool success;
	std::vector<std::string> toolArgs;

	if (!PyArg_ParseTuple(args, "ssOO", &code, &name, &toolArgsList, &callback)) {
		Py_RETURN_NONE;
	}

	if (!PyList_Check(toolArgsList)) {
		/* FIXME */
		Py_RETURN_NONE;
	}

	for (i = 0; i < PyList_Size(toolArgsList); ++i) {
		x = PyList_GetItem(toolArgsList, i);
		if (!PyString_Check(x)) {
			/* FIXME */
			Py_RETURN_NONE;
		}

		toolArgs.push_back(PyString_AsString(x));
	}

	/* The action is deleted automatically.
	 */
	success = clang::tooling::runToolOnCodeWithArgs(new PluginAction(callback), code, toolArgs, name);

	if (!success) {
		Py_RETURN_FALSE;
	}
	Py_RETURN_TRUE;
}

static PyMethodDef methods[] =
{
	{"iterateAST", iterateAST, METH_VARARGS, "Iterate through the AST"},
	{NULL, NULL, 0, NULL}
};

extern "C" PyMODINIT_FUNC initplugin()
{
	PyObject *module __attribute__((unused));

	module = Py_InitModule("plugin", methods);
}

