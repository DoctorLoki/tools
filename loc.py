#!/usr/bin/python 

import os, sys, string

Invalid_Prefixes = [
		".git",
		".svn",
		"vendor",
	]

Valid_Suffixes = [
		".c",
		".h",
		".cc",
		".cpp",
		".hh",
		".hpp",
		".c++",
		".h++",
		".go",
		".java",
		".py",
		".pl",
		#".sh",
		#".bat",
		#"akefile",
		#".conf",
		#".config",
		#".pro",
		#".txt",
		#".html",
	]

def main():
	args = sys.argv[1:]
	if "vendor" in args or "+vendor" in args:
		Invalid_Prefixes.remove("vendor")
	paths = recursively_find_source_files({}, "", os.listdir("."))
	total_files = 0
	total_lines = 0
	total_bytes = 0
	for path in sorted(paths):
		print(path)
		num_lines, num_bytes = count_lines_and_bytes(path)
		total_files += 1
		total_lines += num_lines
		total_bytes += num_bytes
	print("Lines of code: " + str(total_lines) + " Number of bytes: " + str(total_bytes) + " Number of files: " + str(total_files))

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

