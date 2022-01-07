#!/usr/bin/python

# Reformat input into columns, each part spaced 2 spaces apart.

import os, sys, string

def main():
	args = sys.argv[1:]
	sep = "  "
	f = sys.stdin
	if "--tab" in args:
		sep = "\t"
		args.remove("--tab")
	if len(args) == 1:
		f = open(args[0])

	lines = f.readlines()
	f.close()

	columnWidths = []
	for line in lines:
		parts = line.split()
		# Set each column's width to the maximum width of anything in that column.
		for i, part in enumerate(parts):
			while i >= len(columnWidths):
				columnWidths.append(0)
			if len(part) > columnWidths[i]:
				columnWidths[i] = len(part)
	for line in lines:
		s = ""
		parts = line.split()
		for i, part in enumerate(parts):
			s += part
			rem = columnWidths[i] - len(part)
			s += " " * rem
			if i < len(parts) - 1:
				s += sep
		print(s)

if __name__ == "__main__":
	main()


