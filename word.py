#!/usr/bin/python

# Usage:
# word.py n filename.txt
# word.py n < filename.txt
# cat filename.txt | word.py n
#
# Print the nth word on each line, where n is 0-indexed.
# If n is negative, count words from the end of each line instead.
# E.g. ls -lrt | word.py -1
# will print filenames in reverse time order (except those containing spaces).

import os, sys, string

def main():
	f = sys.stdin
	if len(sys.argv) > 1:
		n = int(sys.argv[1])
	for line in f:
		parts = line.split()
		if 0 <= n < len(parts):
			print(parts[n])
		elif -len(parts) <= n < 0:
			print(parts[n])
		else:
			print()

if __name__ == '__main__':
	main()

