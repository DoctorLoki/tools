#!/usr/bin/python 

import os, sys, string, json

INDENT_INC = 2

def main():
	fin = sys.stdin
	if len(sys.argv) > 1:
		fin = open(sys.argv[1], "rb")
	fout = sys.stdout

	j = json.load(fin)

	s = pretty_print_json(j)
	print(s)

def pretty_print_json(j, indent=0, first_indent=0):
	s = ""
	if type(j) == type({}):
		s += pretty_print_json_dict(j, indent, first_indent)
	elif type(j) == type([]):
		s += pretty_print_json_array(j, indent, first_indent)
	elif type(j) == type(""):
		s += pretty_print_json_string(j)
	elif type(j) == type(u""):
		s += pretty_print_json_string(j)
	elif type(j) == type(2):
		s += pretty_print_json_int(j)
	elif type(j) == type(3.14):
		s += pretty_print_json_float(j)
	else:
		sys.stderr.write("Error interpreting JSON: " + repr(j) + "\n")
		s += repr(j)
	return s

def pretty_print_json_dict(j, indent=0, first_indent=0):
	s = ""
	s += " " * first_indent
	s += "{\n"

	indent += INDENT_INC
	keys = sorted_keys(j)
	for i, key in enumerate(keys):
		s += " " * indent
		s += pretty_print_json(key) + ": " + pretty_print_json(j[key], indent, 0)
		if i < len(keys) - 1:
			s += ","
		s += "\n"
	indent -= INDENT_INC

	s += " " * indent
	s += "}"
	return s

def sorted_keys(keys):
	keys1 = []
	keys2 = []
	for key in keys:
		if key.lower() in ["id", "uuid"]:
			keys2.append(key) # Sort these later to give diff a chance to match earlier data.
		else:
			keys1.append(key)
	keys1.sort()
	keys2.sort()
	return keys1[:1] + keys2 + keys1[1:] # Insert ids just after the first entry.

def pretty_print_json_array(arr, indent=0, first_indent=0):
	s = ""
	s += " " * first_indent
	s += "[\n"

	indent += INDENT_INC
	for i, val in enumerate(arr):
		s += " " * indent
		s += pretty_print_json(val, indent, 0)
		if i < len(arr) - 1:
			s += ","
		s += "\n"
	indent -= INDENT_INC

	s += " " * indent
	s += "]"
	return s

def pretty_print_json_string(val):
	s = '"'
	s += val
	s += '"'
	return s

def pretty_print_json_int(val):
	s = ""
	s += repr(val)
	return s

def pretty_print_json_float(val):
	s = ""
	s += repr(val)
	return s

if __name__ == '__main__':
	main()

