#!/usr/bin/python 

import os, sys, string

Invalid_Prefixes = [
		".git",
		".svn",
		"vendor",
	]


CPP_Suffixes = [
		".c",
		".h",
		".cc",
		".cpp",
		".hh",
		".hpp",
		".c++",
		".h++",
	]

ProgLang_Suffixes = [
		".go",
		".java",
		".py",
		".pl",
	]

Script_Suffixes = [
		".sh",
		".bat",
		"akefile",
		".conf",
		".config",
		".pro",
		".yml",
		".yaml",
	]

Valid_Suffixes = CPP_Suffixes + ProgLang_Suffixes + Script_Suffixes

Var_Name_Chars = string.uppercase + string.lowercase + string.digits + "_"

def main():
	paths = recursively_find_source_files({}, "", os.listdir("."))
	total_lines = 0
	total_bytes = 0
	for path in sorted(paths):
		print path
		num_lines, num_bytes = count_lines_and_bytes(path)
		total_lines += num_lines
		total_bytes += num_bytes
	print "Lines of code:", total_lines, "Number of bytes:", total_bytes

def count_lines_and_bytes(path):
	num_lines = 0
	num_bytes = 0
	var_name = None
	prev = None
	for line in open(path):
		num_lines += 1
		num_bytes += len(line)

		# Scan line for whitespace varname whitespace :=
		w = 0
		while w < len(line) and line[w] in " \t": w += 1
		v = w
		while v < len(line) and line[v] in Var_Name_Chars: v += 1
		u = v
		while u < len(line) and line[u] in " \t": u += 1
		t = u

		# Compare with previous line's var_name (if any).
		if t >= len(line) or line[t] not in ":=":
			# Not an assignment. Ignore and reset.
			var_name = None
		elif line[t:t+2] == "::" and has_suffix(path, CPP_Suffixes):
			# Not an assignment. Ignore and reset.
			var_name = None
		elif v == w:
			# No variable name on this line. Ignore and reset.
			var_name = None
		elif var_name == None:
			# No variable name on previous line. Remember this line's variable name.
			var_name = line[:v]
		elif var_name == line[:v]:
				# Match found. Report.
				print "\tDuplicated variable usage in adjacent lines %d and %d:" % (num_lines - 1, num_lines)
				print "\t\t" + prev[:-1]
				print "\t\t" + line[:-1]
				# Keep var_name in case it happens again.
		else:
			# Replace with this line's variable name.
			var_name = line[:v]

		prev = line

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
		paths[path] = name
	return paths

def has_prefix(s, prefix_list):
	for prefix in prefix_list:
		if s[:len(prefix)] == prefix:
			return 1
	return 0

def has_suffix(s, suffix_list):
	for suffix in suffix_list:
		if s[-len(suffix):] == suffix:
			return 1
	return 0

if __name__ == "__main__":
	main()

