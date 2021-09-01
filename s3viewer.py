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
GetACLFmt        = "aws s3api get-object-acl --bucket={BUCKET} --key={KEY} 2>/dev/null"
GetACLFmtPretty  = "aws s3api get-object-acl --bucket={BUCKET} --key={KEY}"
ItemFmt = "% 5d) %s %-15s % 12s %-10s %-8s %s"

Flags = {}

def main():
	args = sys.argv[1:]
	for flag in ["debug", "-debug", "--debug"]:
		if flag in args:
			Flags["debug"] = open("s3viewer.log", "a")
			break
	for flag in ["quiet", "-q", "-quiet", "--quiet"]:
		if flag in args:
			Flags["quiet"] = True
			break

	s3viewer = S3Viewer()
	s3viewer.loop()

class S3Viewer:
	def __init__(self):
		self.cache = {}
		self.levels = []
		self.folders = []
		self.files = []
		self.filter_name = None
		self.filter_owner = None
		self.include_owner = False

	def form_path(self):
		path = "/".join(self.levels)
		if path != "" and path[-1] != '/':
			path += "/"
		return path

	def read_current_path(self):
		path = self.form_path()
		if path in self.cache:
			self.folders, self.files = self.cache[path]
		else:
			self.folders, self.files = ls(path, self.include_owner)
			self.cache[path] = (self.folders, self.files)

	def print_current_path(self):
		self.print_folder(self.folders, self.files)
		self.print_back_option()
		self.print_filter_settings()

	def print_specific_folder(self, path):
		if path in self.cache:
			folders, files = self.cache[path]
		else:
			folders, files = ls(path)
		self.print_folder(folders, files)
		self.print_back_option()
		self.print_filter_settings()

	def print_folder(self, folders, files):
		i = 0
		for date, time, owner, size, name in folders:
			i += 1
			if self.filter_name and self.filter_name not in name:
				continue
			if self.filter_owner and self.filter_owner not in owner:
				continue
			println(ItemFmt % (i, "drwx", owner, "", date, time, name + "/"))
		for date, time, owner, size, name in files:
			i += 1
			if self.filter_name and self.filter_name not in name:
				continue
			if self.filter_owner and self.filter_owner not in owner:
				continue
			println(ItemFmt % (i, "-rw-", owner, size, date, time, name))

	def print_back_option(self):
		if len(self.levels) == 0:
			println("% 5d) exit" % 0)
		else:
			println("% 5d) back" % 0)

	def print_filter_settings(self):
		if self.filter_name and self.filter_owner:
			println(" Note: above filtered by name %r and owner %r" % (self.filter_name, self.filter_owner))
		elif self.filter_name:
			println(" Note: above filtered by name %r" % (self.filter_name))
		elif self.filter_owner:
			println(" Note: above filtered by owner %r" % (self.filter_owner))

	def loop(self):
		action = "list"
		while action != "exit":
			if action == "list":
				self.read_current_path()
				self.print_current_path()
				# Now clear the name filtering, so it's a once-off.
				self.filter_name = None
			action = self.prompt_for_choice()

	def prompt_for_choice(self):
		self.include_owner = False

		try:
			sys.stdout.write("Choose: ")
			sys.stdout.flush()
			choice = ""
			while choice == "": 
				line = sys.stdin.readline()
				line = line[:-1] if line[-1:] == "\n" else line # Trim off trailing "\n".
				args = line.split()      # Sometimes we just want an array of args.
				choice = " ".join(args)  # Sometimes want the line with one space between each arg.
		except:
			println("\nExiting...")
			return "exit"

		if line and line[:1] == "/":
			# /name means search for that name within the names of folders and files.
			self.filter_name = line[1:]
			return "list"

		if line and line[:1] == "@":
			# @owner means search for that owner within the list of folders and files.
			self.filter_owner = line[1:]
			return "list"

		if choice == "ls":
			return "list"

		if choice in ["ls -la", "ls -a"]:
			# ls -la means include ownership data in the next listing.
			path = self.form_path()
			if path in self.cache:
				self.folder, self.files = self.cache[path]
				if not self.files or not self.files[0] or not self.files[0][2]: # owner is missing
					del self.cache[path] # remove cached entry to force loading of owner info
			self.include_owner = True
			return "list"

		if choice in ["ls -laR", "ls -lRa", "ls -alR", "ls -Rla", "ls -aRl", "ls -Ral", "ls -aR", "ls -Ra"]:
			# ls -laR means include ownership data and recursively explore all subfolders.
			self.folders, self.files = ls_laR("/".join(self.levels))
			self.print_current_path()
			return "prompt"

		if choice in ["ls *"]:
			limit = None
			folders_to_scan = self.folders[:]
			if len(folders_to_scan) > 10:
				msgfmt = "Are you sure you want to list %d folders or type a numeric limit? (y/n/42) "
				sys.stdout.write(msgfmt % (len(folders_to_scan)))
				sys.stdout.flush()
				response = sys.stdin.readline().strip().lower()
				if response[:1] in "0123456789":
					limit = int(response)
				elif response[:1] != 'y':
					return "prompt"
			include_owner = ("a" in choice)
			if limit != None:
				folders_to_scan = folders_to_scan[:limit]
			base = self.form_path()
			for folder in folders_to_scan:
				self.folders = []
				self.files = []
				foldername = folder[-1] + "/"
				path = base + foldername
				folders, files = ls(path, include_owner)
				for date, time, owner, size, name in folders:
					self.folders.append((date, time, owner, size, foldername + name))
				for date, time, owner, size, filename in files:
					self.files.append((date, time, owner, size, foldername + filename))
				self.print_folder(self.folders, self.files)
			self.print_back_option()
			self.print_filter_settings()
			return "prompt"

		if choice[:3] == "ls " and choice[-2:] == " *": # ls *, ls -laR *, etc
			limit = None
			if len(self.folders) > 10:
				sys.stdout.write("Are you sure you want to list %d folders or type a numeric limit? (y/n/42) " % (len(self.folders)))
				sys.stdout.flush()
				response = sys.stdin.readline().strip().lower()
				if response[:1] in "0123456789":
					limit = int(response)
				elif response[:1] != 'y':
					return "prompt"
			include_owner = ("a" in choice)
			recursive = ("R" in choice)
			if recursive:
				folders_to_scan = self.folders
			else:
				folders_to_scan = self.folders[:]
			if limit != None:
				folders_to_scan = self.folders[:limit]
			#self.folders = []
			#self.files = []
			base = self.form_path()
			for folder in folders_to_scan:
				foldername = folder[-1] + "/"
				path = base + foldername
				if path in self.cache:
					folders, files = self.cache[path]
				else:
					folders, files = ls(path, include_owner)
					self.cache[path] = (folders, files)
				for date, time, owner, size, name in folders:
					self.folders.append((date, time, owner, size, foldername + name))
				for date, time, owner, size, filename in files:
					self.files.append((date, time, owner, size, foldername + filename))
			self.print_folder(self.folders, self.files)
			self.print_back_option()
			self.print_filter_settings()
			return "prompt"

		if choice == "cd .":
			return "prompt"

		if choice == "cd ..":
			if len(self.levels) == 0:
				return "prompt"
			self.levels = self.levels[:-1]          # cd ..
			return "list"

		if len(args) == 2 and args[0] == "cd":
			subdir = args[1]
			if subdir and subdir[-1] == "/":
				subdir = subdir[:-1]
			found = []
			for date, time, owner, size, foldername in self.folders:
				if subdir and subdir[-1] == '*':
					if foldername[:len(subdir)-1] == subdir[:-1]:
						found.append(foldername)
				elif foldername == subdir:
					found.append(foldername)
			if len(found) == 0:
				println("Found no matches, check that subdirectory name.")
				return "prompt"
			if len(found) == 1:
				self.levels.append(found[0])        # cd subdir
				return "list"
			println("Too many matches, try narrowing your search.")
			return "prompt"

		if choice == "pwd":
			println("/".join(self.levels) + "\n")
			return "prompt"

		try:
			num = int(choice)
		except:
			println("Option not found: %r" % choice)
			return "prompt"

		if num < 0:
			println("Invalid option: negative numbers not allowed")
			return "prompt"

		if num == 0:
			# 0 means go up a level, i.e. cd ..
			if len(self.levels) == 0:               # already at root
				return "exit"
			self.levels = self.levels[:-1]          # cd ..
			return "list"

		num -= 1 # ignore 0 option
		if num < len(self.folders):
			# Folders are listed first, so choosing one means go there, i.e. cd foldername
			self.levels.append(self.folders[num][-1]) # cd foldername
			return "list"

		num -= len(self.folders)
		if num < len(self.files):
			# Files are listed next, choosing one asks whether to copy it to local disk.
			filename = self.files[num][-1]
			sys.stdout.write("Copy file: %s ? (y/n) " % (filename))
			sys.stdout.flush()
			if sys.stdin.readline().strip().lower()[:1] != 'y':
				return "prompt"
			# Copy the file to the local file system, within a created directory tree.
			path = self.form_path()
			destpath = make_all_dirs(path)
			if destpath == None:
				return "prompt"
			cmd = cmdfmt(path + "/" + filename, destpath, CopyCmdFmt)
			println(cmd)
			os.system(cmd)
			return "prompt"

		println("Invalid option")
		return "prompt"

def get_owner(bucket, key):
	cmd = GetACLFmt.replace("{BUCKET}", bucket).replace("{KEY}", key)
	try:
		if "quiet" not in Flags:
			println(GetACLFmtPretty.replace("{BUCKET}", bucket).replace("{KEY}", key))
		f = os.popen(cmd)
		data = f.read()
		f.close()
	except:
		println("Could not popen %s" % (cmd))
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
		if "quiet" not in Flags:
			println(cmdfmt(path, "", ListCmdFmtPretty))
		f = os.popen(cmd)
		lines = f.readlines()
		f.close()
	except:
		println("Could not popen %s" % (cmd))
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
		println("Could not understand line: " + line)
		continue
	return folders, files

def ls_laR(path):
	if path and path[-1] != '/':
		path += "/"
	folders, files = ls(path, include_owner=True)

	all_folders = []
	all_files = []

	for folder in folders:
		date, time, owner, size, foldername = folder
		all_folders.append((date, time, owner, size, path + foldername))

	for filedata in files:
		date, time, owner, size, filename = filedata
		all_files.append((date, time, owner, size, path + filename))

	for folder in folders:
		date, time, owner, size, foldername = folder
		sub_folders, sub_files = ls_laR(path + foldername)
		all_folders += sub_folders
		all_files += sub_files

	return all_folders, all_files

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
			println("mkdir '%s'" % (destpath))
		if not mkdir(destpath):
			println("Could not create destination path " + destpath)
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

def println(line):
	sys.stdout.write(line)
	sys.stdout.write("\n")
	sys.stdout.flush()

	if "debug" in Flags:
		debug = Flags["debug"]
		debug.write(line)
		debug.write("\n")
		debug.flush()

if __name__ == "__main__":
	main()

