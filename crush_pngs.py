#!/usr/bin/python

# Usage crush_png.py [-f] srcdir

import os, sys, string

def main():
	progname = sys.argv[0]

	srcdir = None
	force_overwrite = 0
	for arg in sys.argv[1:]:
		if arg in ["-f", "--force"]:
			force_overwrite = 1
			continue
		if arg[:1] == "-":
			print(progname + ": unknown parameter: " + arg)
			return
		srcdir = arg

	if srcdir == None:
		print("usage: " + progname + " [-f] srcdir")
		return
	while srcdir[-1:] in "/\\":
		srcdir = srcdir[:-1]

	outdir = srcdir + "_crushed/"
	srcdir += "/"


	cmd = 'pngcrush -d ' + outdir + ' -m 0 '
	sources = sorted(os.listdir(srcdir))
	try:
		finished = os.listdir(outdir)
	except:
		os.system("mkdir " + outdir)
		print(progname + ": created " + outdir)
	for filename in sources:
		print(progname + ": crushing " + filename)
		if filename in finished:
			if force_overwrite:
				pass
			else:
				print(progname + ": skipped!")
				continue
		os.system(cmd + srcdir + filename)

if __name__ == '__main__':
	main()

