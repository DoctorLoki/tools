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
import json

ListCmdFmt       = "aws s3 ls {PATH} 2>/dev/null"
ListCmdFmtPretty = "aws s3 ls {PATH}"
CopyCmdFmt       = "aws s3 cp {PATH} {DESTPATH}"
ItemFmt = "% 5d) %-15s % 12s %-10s %-8s %s"

def main():
	cache = {}
	levels = []
	print(cmdfmt("", "", ListCmdFmtPretty))
	folders, files = ls("")
	cache[""] = (folders, files)
	filtertext = None
	while True:
		include_owner = False
		i = 0
		for date, time, owner, size, name in folders:
			i += 1
			if filtertext and filtertext not in name:
				continue
			print(ItemFmt % (i, owner, "", date, time, name + "/"))
		for date, time, owner, size, name in files:
			i += 1
			if filtertext and filtertext not in name:
				continue
			print(ItemFmt % (i, owner, size, date, time, name))
		if len(levels) == 0:
			print("% 5d) exit" % 0)
		else:
			print("% 5d) back" % 0)
		while True:
			filtertext = None
			try:
				sys.stdout.write("Choose: ")
				sys.stdout.flush()
				result = ""
				while result == "": 
					result = sys.stdin.readline()
					result = result.strip()
				if result and result[:1] == "/":
					# /text means search for that text in the list of folders and files.
					filtertext = result[1:]
					break
				if result == "ls -la":
					# ls -la means include ownership data in listings from now on.
					if path in cache:
						folder, files = cache[path]
						if not files or not files[0] or not files[0][2]: # owner is missing
							del cache[path] # remove cached entry to force loading of owner info
					include_owner = True
					break
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
			folders, files = ls(path, include_owner)
			cache[path] = (folders, files)

def get_owner(bucket, key):
	cmd = "aws s3api get-object-acl --bucket %s --key %s" % (bucket, key)
	try:
		print(cmd)
		f = os.popen(cmd)
		data = f.read()
		f.close()
	except:
		print("Could not popen %s" % (cmd))
		return None

	try:
		j = json.loads(data)
		if "Owner" in j and "DisplayName" in j["Owner"]:
			return j["Owner"]["DisplayName"]
	except:
		pass
	return None

def get_bucket(path):
	if path and path[:5] == "s3://":
		path = path[5:]
	if "/" not in path:
		return path
	return path[:path.find("/")]

def get_key(path):
	if path and path[:5] == "s3://":
		path = path[5:]
	if "/" not in path:
		return ""
	return path[path.find("/")+1:]

def ls(path, include_owner=False):
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
			# Buckets
			foldername = parts[-1].strip()
			if foldername[-1] == '/':
				foldername = foldername[:-1]
			date = time = owner = size = ""
			folders.append((date, time, owner, size, foldername))
			continue
		elif len(parts) == 3:
			# Folders
			date, time, size, foldername = parts[0], parts[1], None, parts[-1]
			if foldername[-1] == '/':
				foldername = foldername[:-1]
			owner = ""
			folders.append((date, time, owner, size, foldername))
			continue
		elif len(parts) >= 4:
			# Files
			date, time, size = parts[0], parts[1], parts[2]
			pos = line.find(size, len(date)+1+len(time)+1)
			if pos > 0:
				filename = line[pos+len(size)+1:]
				owner = ""
				if include_owner:
					owner = get_owner(get_bucket(path), get_key(path + filename))
				files.append((date, time, owner, size, filename))
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

