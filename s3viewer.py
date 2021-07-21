#!/usr/bin/python 

# First, run:
#   aws-adfs login --profile dev
# or whatever equivalent you need to get access to S3.
# You may need to also do one of the following for example:
#   export AWS_PROFILE=dev
# or
#   export AWS_PROFILE=devrw
#
# Then run this program to list the S3 contents available to you.

import os, sys, string

CmdFmt       = "aws s3 ls {PATH} 2>/dev/null"
CmdFmtPretty = "aws s3 ls {PATH}"
ItemFmt = "% 5d) %-10s %-8s % 12s %s"

def main():
	cache = {}
	levels = []
	folders, files = ls("")
	cache[""] = (folders, files)
	while True:
		i = 0
		for date, time, size, name in folders:
			i += 1
			print(ItemFmt % (i, date, time, "", name + "/"))
		for date, time, size, name in files:
			i += 1
			print(ItemFmt % (i, date, time, size, name))
		print("% 5d) back/exit" % 0)
		while True:
			try:
				sys.stdout.write("Choose: ")
				result = sys.stdin.readline()
				num = int(result)
				if num == 0:
					if len(levels) == 0:
						return
					levels = levels[:-1]            # cd ..
					break
				num -= 1 # ignore 0 option
				if num < len(folders):
					levels.append(folders[num][-1]) # cd foldername
					break
				num -= len(folders)
				if num < len(files):
					print("Filename: %s" % (files[num][-1]))
					continue
				print("Invalid option")
			except:
				print("\nExiting...")
				return
		path = string.join(levels, "/")
		if path and path[-1] != '/':
			path += "/"
		print(cmdfmt(path, CmdFmtPretty))
		if path in cache:
			folders, files = cache[path]
		else:
			folders, files = ls(path)
			cache[path] = (folders, files)

def ls(path):
	cmd = cmdfmt(path)
	try:
		f = os.popen(cmd)
		lines = f.readlines()
		f.close()
	except:
		print("Could not popen %s" % (cmd))
		lines = []

	files = []
	folders = []
	for line in lines:
		if line and line[-1] == '\n':
			line = line[:-1]
		parts = line.split()
		if len(parts) == 2 and parts[0] == "PRE":
			foldername = parts[-1].strip()
			if foldername[-1] == '/':
				foldername = foldername[:-1]
			folders.append(("", "", "", foldername))
			continue
		elif len(parts) == 3:
			date, time, size, foldername = parts[0], parts[1], None, parts[-1]
			if foldername[-1] == '/':
				foldername = foldername[:-1]
			folders.append((date, time, size, foldername))
			continue
		elif len(parts) >= 4:
			date, time, size = parts[0], parts[1], parts[2]
			pos = line.find(size, len(date)+1+len(time)+1)
			if pos > 0:
				filename = line[pos+len(size)+1:]
				files.append((date, time, size, filename))
				continue
		print("Could not understand line: " + line)
		continue
	return folders, files

def cmdfmt(path="", fmt=CmdFmt):
	if path != "" and path[:5] != "s3://":
		path = "s3://" + path
	if path:
		cmd = fmt.replace("{PATH}", "'" + path + "'")
	else:
		cmd = fmt.replace("{PATH}", "")
	return cmd

if __name__ == "__main__":
	main()

