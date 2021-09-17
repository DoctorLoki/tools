#!/usr/bin/python

#
# A simple recursive file revision control system.
# Simple: it's a tiny subset of other revision control systems.
# Recursive: operates on the current working directory and subdirectories.
# 
# Usage:
#
#  Archive.py init
#
#		Create a repository in the current working directory.
#		The repository is a directory named .Archive/ which
#		is only created if it did not already exist.
#		You could just create that directory yourself instead.
#
#  Archive.py
#
#		The normal operation of running the command is to
#		archive all tracked files in this directory and in
#		any subdirectories that have a repository, recursively.
#		Currently "all tracked files" means "all files" in
#		the directory, including binary files. If you don't
#		want that behaviour, move into another directory those
#		files you don't want tracked.
#
#  Archive.py *.c *.h
#
#		Under Linux it's possible to archive only specific files.
#		This will pretend that the directory only contains the
#		specified files, so only they will be archived. This works
#		under Linux because the shell expands globs like *.c to
#		be a list of matching files. It may not work in M$-Windows
#		because the shell there may not automatically expand globs.
#
# Commands:
#
# init                      Create a repository here if not already extant.
#
# Commands not yet implemented:
#
# add <name>                Track a specified file.
# addsuffix <suffix>        Track all files ending in that suffix.
# forget <name>             Ensure a specified file isn't tracked.
# checkin                   Record changes of everything tracked here and down.
# checkin <name>            Record what changed in a specific tracked file/dir.
# checkout <rev>            Check out a specific revision.
# checkout <name> <rev>     Check out a specific revision of a specific file.
#
# When checking in:
#
# If a file's latest version in the repository is identical to
# the file about to be checked in, that file isn't copied.
# Otherwise, the file is copied into the repository.
#
# Timestamps in the repository use an ISO 8601 basic format.
# YyyyymmddThhmmssZ_filename...
# First the letter Y appears, then year, month, and day numbers,
# then the letter T, then the hour, minutes, and seconds numbers,
# then the letter Z, denoting UTC time, then an underscore.
# Following that is the original file's filename.
# (Note there is a Y10K bug inherent in this naming scheme.)
#
# Changeset structure:
#
# Each file is identified by name and a SHA2-384 hash, base64 encoded.
# The hashes are URL-safe and filename-safe, using A...Za...z0...9-_
# Each directory is identified by name and a hash of its files' hashes.
# This is recursive down the directory tree, so tracked subdirectories
# are checked in first, and their hashes accumulated before checking in
# closer to the root.
#
# TO DO:
#
# There's no way to input a checkin message, and no way to store such
# a message in any case. This may be needed one day to support checkout.
#
# There's no way to check out files. You'd have to manually hunt
# through the repo for a file or substring you want (e.g. using grep).
#
# When copying a modified file into the repository:
# The previous version of the file could be replaced by a
# reverse delta. This would save space, and allow recent
# versions to be reconstructed quickly by applying the
# deltas to the most current version of the file.
# Some common sense is needed to handle large binary files.
# 
# Currently hashes are only computed, not yet used to name revisions.
# Since there's currently no way to check out, hashes are not yet used.
# They could in theory also be used to provide an integrity check of
# the repository.
#
# There's currently no config file.
# If there was a config file, it could contain a few options:
#
# Retain: N pattern
# Retain followed by a decimal number and then a pattern
# indicates that only the last N instances matching that pattern
# will be kept in the repository (older instances are auto-deleted!)
# The purpose of this feature is to allow _some_ binary files to be kept,
# while still keeping the size of the repository manageable.
# N could be optional, so the default usage "Retain: pattern" would
# be used to signify a white list of files to keep, e.g. "Retain: *.py".
#
# Ignore: pattern
# Ignore certain glob patterns (and/or perhaps regular expressions).
# E.g. "Ignore: *.exe"
#

import os, sys, string, time, stat
import base64, hashlib

USING_LINUX = (os.sep == '/')

PROGRAM_NAME =       "Archive"
THIS_PROGRAM =       PROGRAM_NAME + ".py"
REPO_DIRNAME = "." + PROGRAM_NAME + "/"
CONFIG_FILE  = "." + PROGRAM_NAME + ".cfg"

DIR_NAME     = "."

COMMANDS_INIT       = ["init"]
COMMANDS_ADD        = ["add"]
COMMANDS_ADDSUFFIX  = ["addsuffix"]

CONFIG_RETAIN       = 'Retain'
CONFIG_IGNORE       = 'Ignore'

EXAMPLE_CONFIG_FILE = '''
Retain: *.c
Retain: *.h
Retain: *.txt
Retain: Makefile
Retain: index.html
Ignore: *.exe
'''

TIMESTAMP_FORMAT = "Y%Y%m%dT%H%M%SZ_"
TIMESTAMP_LENGTH = 18


def main():
	handle_args(sys.argv)

def handle_args(args):
	repository         = REPO_DIRNAME
	subdirs_to_archive = []
	files_to_archive   = []

	for arg in args[1:]:
		handled = 0

		# "init" command: create a repository directory if none exists.
		for param in COMMANDS_INIT:
			if arg == param:
				handled = repo_exists(repository)
				if not handled:
					os.mkdir(repository)
					sys.stdout.write(THIS_PROGRAM + ": made respository directory %s\n" % repository)
					handled = 1
				break
		if handled:
			return

		# "add" command: add to the list of files to be tracked.
		# TO DO
		# Currently there is no need for an add command because
		# all files in the current working directory are assumed
		# to be in the set of files to be tracked and archived.
		for param in COMMANDS_ADD:
			if arg == param:
				# TO DO
				sys.stderr.write(THIS_PROGRAM + ": error: %s command not implemented\n" % param)
				return
		if handled:
			continue

		# "addsuffix" command: add to the list of suffixes to be tracked.
		# TO DO
		# Currently there is no need for an addsuffix command because
		# all files in the current working directory are assumed
		# to be in the set of files to be tracked and archived.
		for param in COMMANDS_ADDSUFFIX:
			if arg == param:
				# TO DO
				sys.stderr.write(THIS_PROGRAM + ": error: %s command not implemented\n" % param)
				return
		if handled:
			continue

		# Parse config file.
		# TO DO
		# Currently there is no need for a config file because
		# all files in the current working directory are assumed
		# to be in the set of files to be tracked and archived.
		# I.e: keep files you don't want tracked in another directory.

		# In lieu of a config file listing what to track,
		# all files in this directory are tracked.
		if is_regular_file(arg) and not is_readable_file(arg):
			sys.stderr.write(THIS_PROGRAM + ": error: could not open file named " + arg + "\n")
			continue
		if ' ' in arg or '\t' in arg or '\n' in arg:
			sys.stderr.write(THIS_PROGRAM + ": error: whitespace in filename " + arg + "\n")
			continue

		# Append the specified argument to what will be archived.
		if is_regular_file(arg):
			files_to_archive.append(arg)
		elif is_directory(arg):
			subdirs_to_archive.append(arg)

	if not repo_exists(repository):
		sys.stderr.write(THIS_PROGRAM + ": error: no repository here, use init command first\n")
		return

	if not files_to_archive:
		subdirs_to_archive, files_to_archive = list_dir_sorted(".")

	now = time.strftime(TIMESTAMP_FORMAT, time.gmtime())
	archive(".", repository, subdirs_to_archive, files_to_archive, now)

# Archive the named subdirs and filenames.
# Return the hash of this directory.
def archive(root, repo, subdirs, filenames, now):
	# Ensure root ends in a slash.
	while root[-1:] in "\\/": root = root[:-1]
	if root[-1:] != '/': root += "/"

	# Ensure repo ends in a slash.
	while repo and repo[-1] in "\\/": repo = repo[:-1]
	if repo[-1:] != '/': repo += "/"

	print("Archiving " + root)

	# Warning: Y10K bug on the next line, because it assumes
	# alphabetically sorted filenames are listed in ascending
	# timestamp order (due to timestamp prefixing each filename).
	reposubdirs, repofiles = list_dir_sorted(root + repo)

	# Examine the repository and form a merged list of all files.
	# The merged list contains all filenames ever stored in the
	# repository, and for each filename it lists all version dates.
	mergedfiles = {}
	for d in repofiles:
		date = d[0:TIMESTAMP_LENGTH]            # Warning: Y10K bug due to
		realfilename = d[TIMESTAMP_LENGTH:]     # using a constant slice size.
		if realfilename not in mergedfiles:
			mergedfiles[realfilename] = []
		mergedfiles[realfilename].append(date)
	
	# Form directory information as we go into the following.
	this_dir_text = ''
	this_dir_hash = ''

	# Process the subdirs, then the filenames, then this dir last.
	processing_order = subdirs + filenames + [DIR_NAME]
	for name in processing_order:
		# Skip any repository directory, of course.
		if name == repo[:-1]:
			continue

		# Get the base filename of this source path.
		src = name
		for sep in '/\\':
			pos = name.rfind(sep)
			if pos >= 0:
				src = src[pos+1:]

		# Obtain the content of the file or directory.
		path = root + name
		try:
			status = os.stat(path)
		except:
			sys.stderr.write(THIS_PROGRAM + ": error: could not stat " + path + "\n")
			continue

		if name == DIR_NAME:
			# Handle "." specially.
			content = this_dir_text
		elif stat.S_ISDIR(status.st_mode):
			# Recursively handle subdirectories.
			subdirs2, filenames2 = list_dir_sorted(path)
			if repo[:-1] not in subdirs2:
				# Only subdirs which hold repos are recursively visited.
				# Subdirs lacking a repo are completely ignored.
				continue
			content = archive(path, repo, subdirs2, filenames2, now)
		elif stat.S_ISREG(status.st_mode):
			# File contents are used to check for changes.
			if not is_readable_file(path):
				sys.stderr.write(THIS_PROGRAM + ": error: could not read " + path + "\n")
				continue
			content = open(path, "rb").read()
		else:
			sys.stderr.write(THIS_PROGRAM + ": error: non-file non-dir " + path + "\n")
			continue # Weird: a non-file non-dir named on command line!

		# Form summary line from a hash, permissions, and name.
		summary = hash384base64(content) + " " + get_mode_str(path) + " " + src + "\n"
		if name == DIR_NAME:
			this_dir_text = summary + this_dir_text # Put "." summary at top.
			content = this_dir_text # Ensure we look for this final form in repo.
		else:
			this_dir_text += summary	# Append summary line at bottom.

		# Decide if the content needs to be stored in the repository.
		store_it = 0
		if src not in mergedfiles:
			# That name not previously seen in the repo! Store it.
			#if stat.S_ISREG(status.st_mode):
				#print("Name not previously seen: " + src)
			store_it = 1
			# Note, subdirectories have already been recursively handled earlier.
		else:
			# Does the latest repo version of the same named file differ?
			dates = mergedfiles[src]
			latest = dates[-1]
			repocontent = open(root + repo + latest + src, "rb").read()
			if content != repocontent:
				# Files are different. Store this new file.
				#print("File is different in repo: " + src)
				store_it = 1
			else:
				# Same file as the last version. Do not store it.
				#print("File is same in repo, skip:" + src)
				store_it = 0
			repocontent = "" # Be memory efficient in case of recursion.

		# Store the content, if necessary.
		if store_it:
			if name == DIR_NAME:
				sys.stdout.write(THIS_PROGRAM + ": storing dir %s\n" % name)
				open(root + repo + now + src, "wb").write(this_dir_text)
				continue

			utc = time.gmtime(status.st_mtime)
			date = time.strftime(TIMESTAMP_FORMAT, utc)
			if stat.S_ISDIR(status.st_mode):
				#sys.stderr.write(THIS_PROGRAM + ": do not store directory here %s\n" % name)
				continue
			elif stat.S_ISLNK(status.st_mode):
				sys.stdout.write(THIS_PROGRAM + ": storing link %s\n" % name)
				if USING_LINUX:
					# Copy underlying data.
					os.system('/bin/cp -p "' + path + '" "' + root + repo + date + src + '"')
				else:
					# Copy the file ourselves (losing permissions and timestamps).
					open(root + repo + date + src, "wb").write(content)
			elif stat.S_ISREG(status.st_mode):
				sys.stdout.write(THIS_PROGRAM + ": storing file %s\n" % name)
				if USING_LINUX:
					# Keep permissions data with the file's inode.
					os.system('/bin/cp -p "' + path + '" "' + root + repo + date + src + '"')
				else:
					# Copy the file ourselves (losing permissions and timestamps).
					open(root + repo + date + src, "wb").write(content)
		else:
			# Content already exists in repository.
			pass
		content = "" # Be memory efficient in case of recursion.

	return this_dir_text

# List subdirectories and filenames in the given path.
# Only report regular files and subdirectories.
# Skip device files, links, and the "." and ".." dirs.
# Return two lists: subdirnames and filenames.
# Each list will be alphabetically sorted.
def list_dir_sorted(dirpath = "."):
	while dirpath and dirpath[-1] in "\\/":
		dirpath = dirpath[:-1]
	names = os.listdir(dirpath)
	subdirnames = []
	filenames = []
	for name in names:
		if name in [".", ".."]: continue
		try:
			status = os.stat(dirpath + os.sep + name)
		except:
			continue
		if stat.S_ISDIR(status.st_mode):   subdirnames.append(name)
		elif stat.S_ISREG(status.st_mode): filenames.append(name)

	subdirnames.sort()
	filenames.sort()

	return (subdirnames, filenames)

def repo_exists(repo, dirpath = "."):
	subdirs, filenames = list_dir_sorted(dirpath)
	while repo and repo[-1] in "\\/":
		repo = repo[:-1]
	if repo in subdirs:
		return 1
	return 0

def is_regular_file(path):
	status = os.stat(path)
	if stat.S_ISREG(status.st_mode):
		return 1
	return 0

def is_directory(path):
	status = os.stat(path)
	if stat.S_ISDIR(status.st_mode):
		return 1
	return 0

def is_readable_file(path):
	try:
		open(path, "rb").close()
		return 1
	except:
		return 0

def get_mode_str(path):
	s = ""
	status = os.stat(path)
	if stat.S_ISDIR(status.st_mode):    s += 'd'
	else:                               s += '-'

	if stat.S_IRUSR & status.st_mode:   s += 'r'
	else:                               s += '-'
	if stat.S_IWUSR & status.st_mode:   s += 'w'
	else:                               s += '-'
	if stat.S_IXUSR & status.st_mode:   s += 'x'
	else:                               s += '-'

	if stat.S_IRGRP & status.st_mode:   s += 'r'
	else:                               s += '-'
	if stat.S_IWGRP & status.st_mode:   s += 'w'
	else:                               s += '-'
	if stat.S_IXGRP & status.st_mode:   s += 'x'
	else:                               s += '-'

	if stat.S_IROTH & status.st_mode:   s += 'r'
	else:                               s += '-'
	if stat.S_IWOTH & status.st_mode:   s += 'w'
	else:                               s += '-'
	if stat.S_IXOTH & status.st_mode:   s += 'x'
	else:                               s += '-'

	return s

def hash384base64(bytes):
    return base64.urlsafe_b64encode(hashlib.sha384(bytes).digest())

if __name__ == '__main__':
	main()

