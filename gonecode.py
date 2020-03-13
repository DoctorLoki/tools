#!/usr/bin/python 

# Usage: gonecode.py
#
# Reports names of functions, types, and global vars that are only seen once in a code base.
# Recursively walks down the directory tree from the current dir.
# Finds all ".go" source files and analyses them looking for orphan funcs and types.
# Only using a simplistic text search.

import os, sys, string

Invalid_Prefixes = [
		".git",
		".svn",
		"vendor",
	]

Valid_Suffixes = [
		".go",
	]

Test_Suffixes = [
		"_test.go",
	]

Ignore_Test_Files  = 0
Ignore_Test_Funcs  = 0
Print_All_Funcs    = 0
Print_All_Types    = 0
Print_All_Vars     = 0
Print_All_Paths    = 0
Print_Line_Counts  = 1
Print_Unused_Funcs = 1
Print_Unused_Types = 1
Print_Unused_Vars  = 1

def main():
	global Ignore_Test_Files, Ignore_Test_Funcs
	global Print_All_Funcs, Print_All_Types, Print_All_Vars, Print_All_Paths, Print_Line_Counts
	global Print_Unused_Funcs, Print_Unused_Types, Print_Unused_Vars

	root = ""
	dirname = "."
	for arg in sys.argv[1:]:
		if is_param(arg, "--ignore-test-files"):  Ignore_Test_Files  ^= 1; continue
		if is_param(arg, "--ignore-test-funcs"):  Ignore_Test_Funcs  ^= 1; continue
		if is_param(arg, "--print-all-funcs"):    Print_All_Funcs    ^= 1; continue
		if is_param(arg, "--print-all-types"):    Print_All_Types    ^= 1; continue
		if is_param(arg, "--print-all-vars"):     Print_All_Vars     ^= 1; continue
		if is_param(arg, "--print-all-paths"):    Print_All_Paths    ^= 1; continue
		if is_param(arg, "--print-line-counts"):  Print_Line_Counts  ^= 1; continue
		if is_param(arg, "--print-unused-funcs"): Print_Unused_Funcs ^= 1; continue
		if is_param(arg, "--print-unused-types"): Print_Unused_Types ^= 1; continue
		if is_param(arg, "--print-unused-vars"):  Print_Unused_Vars  ^= 1; continue
		if arg[:2] == "--": print("Unknown directive: " + arg); return

		# Default is to use a command-line argument as the root of the search.
		dirname = root = arg

	paths = recursively_find_source_files({}, root, os.listdir(dirname))

	total_files = 0
	total_lines = 0
	total_bytes = 0

	all_funcs = {}
	all_types = {}
	all_vars  = {}
	for path in sorted(paths):
		if Print_All_Paths:
			print(path)
		num_lines, num_bytes = count_lines_and_bytes(path)
		find_funcs(path, all_funcs)
		find_types(path, all_types)
		find_vars(path, all_vars)
		total_files += 1
		total_lines += num_lines
		total_bytes += num_bytes

	used_funcs = {}
	if Print_Unused_Funcs:
		for path in sorted(paths):
			find_funcs(path, all_funcs, used_funcs)

	used_types = {}
	if Print_Unused_Types:
		for path in sorted(paths):
			find_types(path, all_types, used_types)

	used_vars = {}
	if Print_Unused_Vars:
		for path in sorted(paths):
			find_vars(path, all_vars, used_vars)

	if Print_All_Funcs:
		print("Funcs:")
		for funcname in sorted(all_funcs):
			func_decls = all_funcs[funcname]
			for func_decl in func_decls:
				path, line_num, receiver_type, name = func_decl
				print("\t%s %s\t%s:%d" % (receiver_type, funcname, path, line_num))

	if Print_Unused_Funcs:
		print("Unused funcs:")
		for funcname in sorted(all_funcs):
			if funcname not in used_funcs:
				print("\t%s\tUNUSED FUNC" % (funcname))
				func_decls = all_funcs[funcname]
				for func_decl in func_decls:
					path, line_num, receiver_type, name = func_decl
					print("\t\t%s %s\t%s:%d" % (receiver_type, funcname, path, line_num))

	if Print_Unused_Types:
		print("Unused types:")
		for typename in sorted(all_types):
			if typename not in used_types:
				print("\t%s\tUNUSED TYPE" % (typename))
				type_decls = all_types[typename]
				for type_decl in type_decls:
					path, line_num, name = type_decl
					print("\t\t%s\t%s:%d" % (typename, path, line_num))

	if Print_Unused_Vars:
		print("Unused vars:")
		for varname in sorted(all_vars):
			if varname not in used_vars:
				print("\t%s\tUNUSED VAR" % (varname))
				var_decls = all_vars[varname]
				for var_decl in var_decls:
					path, line_num, name = var_decl
					print("\t\t%s\t%s:%d" % (varname, path, line_num))

	if Print_Line_Counts:
		print("Lines of code: %d Number of bytes: %d Number of files: %d" % (total_lines, total_bytes, total_files))

def find_funcs(path, funcs, used_funcs = None):
	line_num = 0
	funcname = ""
	for line in open(path):
		line_num += 1

		if line[:1] == "}":						# End-of-func resets which funcname we're within.
			funcname = ""

		line_has_func_decl = (line[:5] == "func ")

		if not line_has_func_decl:
			# Line is not a func declaration.
			if used_funcs != None:
				# Perform func-call/func-use analysis only on lines which are not func declarations.
				for name in funcs:
					if name == funcname:				# Ignore funcs calling themselves.
						continue
					if name not in line:				# Fast approximate check.
						continue
					if name not in split_code(line):	# Slow accurate check.
						continue
					if name not in used_funcs:
						used_funcs[name] = []
					used_funcs[name].append((path, line_num))
			# When looking for usage, don't add func decl again.
			continue

		line = line[5:]							# Trim "func "

		# Look for a receiver.
		receiver_type = ""
		if line[:1] == "(":						# Found start of receiver.
			line = line[1:]						# Trim "("
			pos = line.find(")")
			if pos < 0:							# Cannot understand func declaration.
				continue
			receiver_decl = line[:pos].split()
			if len(receiver_decl) < 1:			# Cannot understand receiver declaration.
				continue
			receiver_type = receiver_decl[-1]	# Keep receiver type.
			line = line[pos+1:]					# Trim receiver and ")"

		# Look for parameter list.
		pos = line.find("(")
		if pos < 0:
			pos = len(line)
		funcname = line[:pos].strip()
		if used_funcs != None:					# Analysing usage; set funcname then continue.
			continue
		if Ignore_Test_Funcs and funcname[:4] == "Test":
			continue
		if funcname not in funcs:
			funcs[funcname] = []
		data = (path, line_num, receiver_type, funcname)
		funcs[funcname].append(data)

	return funcs

def find_types(path, types, used_types = None):
	line_num = 0
	for line in open(path):
		line_num += 1

		line_has_type_decl = (line[:5] == "type ")

		if used_types != None:
			# Perform usage anaylsis.
			if not line_has_type_decl:
				# Perform type-use analysis only on lines which are not type declarations.
				for name in types:
					if name not in line:				# Fast approximate check.
						continue
					if name not in split_code(line):	# Slow accurate check.
						continue
					# Record usage.
					if name not in used_types:
						used_types[name] = []
					used_types[name].append((path, line_num))
			# When looking for usage, don't add type decl again.
			continue

		if not line_has_type_decl:
			continue

		line = line[5:]							# Trim "type "

		# Look for type name.
		typename = line.split()[0]
		if typename not in types:
			types[typename] = []
		data = (path, line_num, typename)
		types[typename].append(data)

	return types

def find_vars(path, vars, used_vars = None):
	line_num = 0
	for line in open(path):
		line_num += 1

		line_has_var_decl = (line[:4] == "var ")

		if used_vars != None:
			# Perform usage analysis.
			if not line_has_var_decl:
				# Perform global var-use analysis only on lines which are not var declarations.
				for name in vars: 
					if name not in line:				# Fast approximate check.
						continue
					if name not in split_code(line):	# Slow accurate check.
						continue
					# Record usage.
					if name not in used_vars:
						used_vars[name] = []
					used_vars[name].append((path, line_num))
			# When looking for usage, don't add var decl again.
			continue

		if not line_has_var_decl:
			continue

		line = line[4:]							# Trim "var "

		# Look for var name.
		parts = split_vars(line)
		for varname in parts:
			if varname == "(":
				continue						# Ignore "var ("
			if varname not in vars:
				vars[varname] = []
			data = (path, line_num, varname)
			vars[varname].append(data)

	return vars

def count_lines_and_bytes(path):
	num_lines = 0
	num_bytes = 0
	for line in open(path):
		num_lines += 1
		num_bytes += len(line)
	return num_lines, num_bytes

def recursively_find_source_files(paths, root, names):
	for name in names:
		if has_prefix(name, Invalid_Prefixes):
			continue
		path = root + "/" + name if root else name
		try:
			subnames = os.listdir(path)
			paths = recursively_find_source_files(paths, path, subnames)
			continue
		except:
			pass
		if not has_suffix(name, Valid_Suffixes):
			continue
		if Ignore_Test_Files and has_suffix(name, Test_Suffixes):
			continue
		paths[path] = name
	return paths

def is_param(s, param, significant=0):
	simple = s.replace('_', '-')
	if significant > 0:
		if has_prefix(simple, [param[:significant]]):
			return True
	elif simple == param:
		return True
	return False

def split_code(line):
	puncts = "(){}[]<>*.-+=!~^&|,:;\t\r\n"
	simple = line
	for ch in puncts:
		simple = simple.replace(ch, ' ')
	return simple.split()

def split_vars(line):
	for stopword in ["//", ":=", "="]:
		pos = line.find(stopword)
		if pos >= 0:
			line = line[:pos]
	return split_code(line)

def has_prefix(s, prefix_list):
	for prefix in prefix_list:
		if s[:len(prefix)] == prefix:
			return True
	return False

def has_suffix(s, suffix_list):
	for suffix in suffix_list:
		if s[-len(suffix):] == suffix:
			return True
	return False

if __name__ == "__main__":
	main()

