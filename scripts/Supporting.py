#! /usr/bin/python

# Copyright (c) 2013-2017 Ardexa Pty Ltd
#
# This code is licensed under the MIT License (MIT).
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
#

# Supporting script Vers: 1.5.5
# Dated 9 Jan 2018
#


import os
import sys
import time
from subprocess import Popen, PIPE, STDOUT

#	This function logs a line of data to both a 'log' file, and a 'latest' file
#	The 'latest' file is optional, and is sent to this function as a boolean value via  
#	the variable 'require_latest'. 
#	So the 2 log directories and filenames are:
#		a. (REQUIRED): log_directory + log_filename
#		b.	(OPTIONAL): latest_directory + latest_filename
#		
#	The 'latest' directory and filename is provided so as to have a consistent file of the latest events
#	This is usually the latest day of events. 
#	The way this function works with the 'latest' log_dir is as follows:
# 		a. It checks for the existance of log_directory + log_filename
#		b.	If (a) doesn't exist, then any 'latest' file is removed and a new one created
#		c.	If (a) already exists, logs are written to any existing 'latest' file
#			If one doesn't exist, it will be created
#
#	For both the 'log' and 'latest' files, a header line will be written if a new file is created
#	Please note that a header must start with the '#' symbol, so the Ardexa agent can interpret this line as a header
#  entry, and will not send it to the cloud
#
def write_log(log_directory, log_filename, header, logline, debug, require_latest, latest_directory, latest_filename):
	create_new_file = False

	# Make sure the logging directory exists. The following will create all the necessary subdirs, 
	# if the subdirs exist in part or in full
	if not os.path.exists(log_directory):
		os.makedirs(log_directory)
	full_path_log = os.path.join(log_directory, log_filename)
	if (debug > 1):
		print "Full path of log directory: ", full_path_log
	# If the file doesn't exist, annotate that a new 'latest' file is to be created
	# and that a header is to be created
	if not (os.path.isfile(full_path_log)):
		if (debug > 1):
			print "Log file doesn't exist: ", full_path_log
		create_new_file = True

	# Repeat for the 'latest', if it doesn't exist
	if (require_latest):
		if not os.path.exists(latest_directory):
			os.makedirs(latest_directory)
		full_path_latest = os.path.join(latest_directory, latest_filename)
		if (debug > 1):
			print "Full path of latest directory: ", full_path_latest
		# If the 'create_new_file' tag is set AND the file exists, then remove it
		if ((create_new_file) and (os.path.isfile(full_path_latest))):
			# then remove the file
			os.remove(full_path_latest)


	# Now create both (or open both) and write to them
	if (debug > 1):
		print "##########################################"
		print "Writing the line to", full_path_latest
		print logline
		print "##########################################"

	# Write the logline to the log file
	write_log = open(full_path_log,"a")
	if (create_new_file):
		write_log.write(header)
	write_log.write(logline)
	write_log.close()

	# And write it to the 'latest' if required
	if (require_latest):
		write_latest = open(full_path_latest,"a")
		if (create_new_file):
			write_latest.write(header)
		write_latest.write(logline)
		write_latest.close()
		


# Check that a process is not running more than once, using PIDFILE
def check_pidfile(pidfile, debug):

	# Check PID exists and see if the PID is running
	if os.path.isfile(pidfile):
		pidfile_handle = open(pidfile, 'r')
		# try and read the PID file. If no luck, remove it
		try:
			pid = int(pidfile_handle.read())
			pidfile_handle.close()
			if (check_pid(pid, debug)):
				return True
			else:
				# PID is not active, remove the PID file
				os.unlink(pidfile)
		except:
			os.unlink(pidfile)

	# Create a PID file, to ensure this is script is only run once (at a time)
	pid = str(os.getpid())
	file(pidfile, 'w').write(pid)

	return False

# This function will check whether a PID is currently running
def check_pid(pid, debug):  	

	try:
		# A Kill of 0 is to check if the PID is active. It won't kill the process
		os.kill(pid, 0)
		if (debug > 1):
			print "Script has a PIDFILE where the process is still running"
		return True
	except OSError:
		if (debug > 1):
			print "Script does not appear to be running"
		return False


# Check the correct number of arguments, and if so, return them
# Otherwise return an empty list
def check_args(number_of_args):
	empty = []
	# Make sure there are the correct number of arguments
	# Remember to add to the arguments list
	number_of_args = number_of_args + 1
	if (len(sys.argv) != number_of_args):
		print "There can only be: ", number_of_args, " arguments"
		return empty
	else:
		# return the arguments
		return sys.argv

# This function just gets the time
def get_datetime():
	dt = time.strftime('%Y-%m-%dT%H:%M:%S%z')
	return dt


# Convert a string to INT
def convert_to_int(value):
	try:
		ret_val = int(value)
		return True, ret_val
	except ValueError:
		return False, -1

# Convert a string to FLOAT
def convert_to_float(value):
	try:
		ret_val = float(value)
		return True, ret_val
	except ValueError:
		return False, -1


# This function will disown, so the Ardexa service can be restarted
def disown(debug):
	# Get the current PID
	pid = os.getpid()
	cgroup_file = "/proc/" + str(pid) + "/cgroup"
	try:
		infile = open(cgroup_file, "r") 
	except IOError:
		print "Could not open cgroup file: ",cgroup_file
		return False

	# Read each line
	for line in infile:
		# Check if the line contains "ardexa.service"
		if (line.find("ardexa.service") == -1):
			continue

		# if the lines contains "name=", replace it with nothing
		line = line.replace("name=", "")
		# Split  the line by commas
		items_list = line.split(':')
		accounts = items_list[1]
		dir_str = accounts + "/ardexa.disown"
		# If accounts is empty, continue
		if (not accounts):
			continue

		# Create the dir and all subdirs
		full_dir = "/sys/fs/cgroup/" + dir_str
		if not os.path.exists(full_dir):
			os.makedirs(full_dir)
			if (debug >= 1):
				print "Making directory: ", full_dir
		else:
			if (debug >= 1):
				print "Directory already exists: ", full_dir

		# Add the PID to the file
		full_path = full_dir + "/cgroup.procs"
		prog_list = ["echo", str(pid), ">", full_path]
		run_program(prog_list, debug, True)

		# If this item contains a comma, then separate it, and reverse 
		# some OSes will need cpuacct,cpu reversed to actually work
		if (accounts.find(",") != -1):
			acct_list= accounts.split(',')
			accounts = acct_list[1] + "," + acct_list[0]
			dir_str = accounts + "/ardexa.disown"
			# Create the dir and all subdirs. But it may not work. So use a TRY
			full_dir = "/sys/fs/cgroup/" + dir_str
			try:
				if not os.path.exists(full_dir):
					os.makedirs(full_dir)
			except:
				continue

			# Add the PID to the file
			full_path = full_dir + "/cgroup.procs"
			prog_list = ["echo", str(pid), ">", full_path]
			run_program(prog_list, debug, True)
			
	infile.close()

	# For debug purposes only
	if (debug >= 1):
		prog_list = ["cat", cgroup_file]
		run_program(prog_list, debug, False)

	# If there are any "ardexa.service" in the proc file. If so, exit with error
	prog_list = ["grep", "-q", "ardexa.service", cgroup_file]
	if (run_program(prog_list, debug, False) == True):
		# There are entries still left in the file
		return False
	else:
		return True
	

# Run a  program and check program return code
# Note that some commands don't work well with Popen. 
# So if this function is specifically called with 'shell=True', then it
# will run the old 'os.system'. In which case, there is no program output
def run_program(prog_list, debug, shell):

	try:
		if (not shell):
			process = Popen(prog_list, stdout=PIPE, stderr=PIPE)
			output, error = process.communicate()
			retcode = process.returncode
			if (debug >= 1):
				print "Program : ", " ".join(prog_list)," Return Code: ", retcode, " and output: ",output
			if (retcode == 0):
				return True
			else:
				return False
		else:
			command = " ".join(prog_list)
			os.system(command)
			return True
	except:
		return False




