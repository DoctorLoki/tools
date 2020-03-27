#!/usr/bin/python 

import os, sys, string

def main():
	indent = 0
	fin = sys.stdin
	if len(sys.argv) > 1:
		fin = open(sys.argv[1], "rb")
	fout = sys.stdout
	lines = fin.readlines()
	outside = 1
	s = ""
	for line in lines:
		if outside:
			if line and line.strip() and line.strip()[0] == '{':
				outside = 0
			else:
				print line
				continue
		s = ""
		n = 0
		prev = ''
		while n < len(line):
			ch = line[n]
			if n+1 < len(line):
				next = line[n+1]
			else:
				next = ''
			n += 1

			s += ch
			if ch in "{[":
				fout.write(" " * indent)
				fout.write(s + "\n")
				s = ""
				indent += 2
			elif ch in "]}":
				if next in [",", "\n"]: # include it in this line
					n += 1
					ch = next
					next = ''
					s += ch
				if prev in ["]", "}"]:
					indent -= 2
				fout.write(" " * indent)
				fout.write(s + "\n")
				s = ""
				if prev not in ["]", "}"]:
					indent -= 2
			elif ch == ",":
				fout.write(" " * indent)
				fout.write(s + "\n")
				s = ""

			prev = ch
	if s:
		print s

if __name__ == '__main__':
	main()

