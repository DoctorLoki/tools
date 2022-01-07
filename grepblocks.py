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
	distance = 7
	sought = []
	for arg in sys.argv[1:]:
		if arg and arg[0] in "0123456789":
			distance = int(arg)
			continue
		sought.append(arg)

	if len(sought) == 0:
		print("usage: %s word1 [word2 ...]" % sys.argv[0])
		return

	paths = recursively_find_source_files({}, "", os.listdir("."))
	for path in sorted(paths):
		blocks = find_blocks_containing_words(path, distance, sought)
		if len(blocks) == 0:
			continue
		#print(path)
		for block in blocks:
			print(path + ": " + repr(block))

def find_blocks_containing_words(path, distance, sought):
	# "Blocks" are simply defined by the distance parameter
	# as number of lines from the first line containing a sought word
	# to the last line containing a sought word.
	blocks = []
	remaining = sought[:]
	f = open(path)
	lines = f.readlines()
	block = []
	for i, line in enumerate(lines):
		word = contains_any(line, remaining[:1])
		if len(block) > 0:
			block.append(line)
		if len(block) > distance: # Too long!
			block = []
			remaining = sought[:] # Restart searching.
			continue
		if word == None:
			continue
		if len(block) == 0:
			block.append(line)
		remaining.remove(word)
		if len(remaining) == 0:
			blocks.append(block)
			block = []
			remaining = sought[:] # Restart searching.
	return blocks

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

def contains_any(line, words):
	for word in words:
		if word in line:
			return word
	return None

if __name__ == "__main__":
	main()

