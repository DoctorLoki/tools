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

ListCmdFmt       = "aws s3 ls {PATH} 2>/dev/null"
ListCmdFmtPretty = "aws s3 ls {PATH}"
CopyCmdFmt       = "aws s3 cp {PATH} {DESTPATH}"
ItemFmt = "% 5d) %-10s %-8s % 12s %s"

def main():
	cache = {}
	levels = []
	print(cmdfmt("", "", ListCmdFmtPretty))
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
		if len(levels) == 0:
			print("% 5d) exit" % 0)
		else:
			print("% 5d) back" % 0)
		while True:
			try:
				sys.stdout.write("Choose: ")
				sys.stdout.flush()
				result = sys.stdin.readline()
				num = int(result)
				if num == 0:
					# 0 means go up a level, i.e. cd ..
					if len(levels) == 0:
						return
					levels = levels[:-1]            # cd ..
					break
				num -= 1 # ignore 0 option
				if num < len(folders):
					# Folders are listed first, so choosing one means go there, i.e. cd foldername
					levels.append(folders[num][-1]) # cd foldername
					break
				num -= len(folders)
				if num < len(files):
					# Files are listed next, choosing one asks whether to copy it to local disk.
					filename = files[num][-1]
					sys.stdout.write("Copy file: %s ? (y/n) " % (filename))
					sys.stdout.flush()
					if sys.stdin.readline().strip().lower()[:1] != 'y':
						continue
					# Copy the file to the local file system, within a created directory tree.
					path = "/".join(levels)
					destpath = make_all_dirs(path)
					if destpath == None:
						continue
					cmd = cmdfmt(path + "/" + filename, destpath, CopyCmdFmt)
					print(cmd)
					os.system(cmd)
					break
				print("Invalid option")
			except:
				print("\nExiting...")
				return

		# List folders and files.
		path = "/".join(levels)
		if path and path[-1] != '/':
			path += "/"
		print(cmdfmt(path, "", ListCmdFmtPretty))
		if path in cache:
			folders, files = cache[path]
		else:
			folders, files = ls(path)
			cache[path] = (folders, files)

def ls(path):
	cmd = cmdfmt(path, "", ListCmdFmt)
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

def cmdfmt(path="", destpath="", fmt=ListCmdFmt):
	if path[:5] != "s3://":
		path = "s3://" + path
	if path:
		cmd = fmt.replace("{PATH}", "'" + path + "'")
	else:
		cmd = fmt.replace("{PATH}", "")
	if destpath:
		cmd = cmd.replace("{DESTPATH}", "'" + destpath + "'")
	else:
		cmd = cmd.replace("{DESTPATH}", ".")
	return cmd

def make_all_dirs(path=""):
	if path != "" and path[:5] == "s3://":
		path = path[5:]
	destpath = "./"
	for subdir in path.split('/'):
		destpath += subdir + "/"
		try:
			os.listdir(destpath)
			continue
		except:
			print("mkdir '%s'" % (destpath))
		if not mkdir(destpath):
			print("Could not create destination path " + destpath)
			return None
	return destpath

def mkdir(dirpath):
	try:
		os.listdir(dirpath)
		return True # Already exists, good.
	except:
		pass
	try:
		os.mkdir(dirpath)
		return True # Created, good.
	except:
		return False # Failed to create, bad.

if __name__ == "__main__":
	main()

