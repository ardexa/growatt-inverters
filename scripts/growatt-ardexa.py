#! /usr/bin/python

# Copyright (c) 2013-2018 Ardexa Pty Ltd
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
# This script will query the Growatt Inverters via Modbus RTU or via Modbus RTU encapsulated over TCP
#
# Usage: python growatt-ardexa.py device port start_address end_address log_directory query_type debug_str
# eg: 
#
# Note: This plugin uses the modpoll tool.
# 		sudo mkdir /opt/modpoll
#		cd /opt/modpoll
#		sudo wget http://www.modbusdriver.com/downloads/modpoll.3.4.zip
#		sudo unzip modpoll.3.4.zip 
#		cd linux/
#		sudo chmod 755 modpoll 
#		sudo cp modpoll /usr/local/bin
#

import sys
import time
import os
from Supporting import *
from subprocess import Popen, PIPE, STDOUT

PIDFILE = 'growatt-ardexa-'
START_REG = "1"
REGS_TO_READ = "42"
BAUD_RATE = "9600"
PARITY = "none"
USAGE = "Usage: python growatt-ardexa.py device port start_address end_address log_directory query_type debug_str"

status_dict = { "0" : "waiting", "1": "normal", "2" : "fault"}
fault_dict = {		"24" : "Auto Test Failed", "25": "No AC Connection", "26" : "PV Isolation Low",
						"27" : " Residual I High", "28": "Output High DCI", "29" : "PV Voltage High"}

#~~~~~~~~~~~~~~~~~~~   START Functions ~~~~~~~~~~~~~~~~~~~~~~~

def read_inverter(device, enc_tcp, ip_address, rtu_address, port, debug):
    # initialise stdout and stderr to NULL
    stdout = ""
    stderr = ""
    errors = False
    register_dict = {}
    header = ""
    output_str = ""


    # NOTE: For the modpoll command, do not use the '-0' option. It will rmeove the 0 reading, which we need

    if (enc_tcp):
        # This command is to get the parameter data from the inverters using RTU encapsulated over TCP
        # modpoll -m enc -a {rtu address} -r {start reg} -c {regs to read} -t 4 -1 -p {PORT} {IP Address}
        # Example: modpoll -m enc -a 3 -r 1 -c 42 -t 4 -1 -0 -p 502 192.168.1.1
        ps = Popen(['modpoll', '-m', 'enc', '-a', rtu_address, '-r', START_REG, '-c', REGS_TO_READ, '-t', '3', '-1', '-p', port, ip_address], stdout=PIPE, stderr=PIPE)
    else:
        # This command is to get the parameter data from the inverters using RTU over an RS485 line
        # modpoll -m rtu -a {rtu address} -r {start reg} -c {regs to read} -t 4 -0 -1 -4 10 -b {BAUD} -p PARITY {device}
        # Example: modpoll -m rtu -a 3 -r 1 -c 42 -t 4 -1 -4 10 -0 -p none -b 9600 /dev/ttyS0
        ps = Popen(['modpoll', '-m', 'rtu', '-a', rtu_address, '-r', START_REG, '-c', REGS_TO_READ, '-t', '3', '-1', '-4', '10', '-p', PARITY, '-b', BAUD_RATE, device], stdout=PIPE, stderr=PIPE)

    stdout, stderr  = ps.communicate()
		
    # Modpoll will send the data to stderr, but also send errors on stderr as well. weird.
    if (debug >= 2):
        print "STDOUT: ", stdout
        print "STDERR: ", stderr

    # for each line, split the register and return values
    for line in stdout.splitlines():
        # if the line starts with a '[', then process it
        if (line.startswith('[')):
            line = line.replace('[','')	
            line = line.replace(']','')	
            register,value = line.split(':')
            register = register.strip()
            value = value.strip()
            register_dict[register] = value


    status = vdc1 = idc1 = vdc2 = idc2 = pac = freq = vac1 = vac2 = vac3 = pdc1 = pdc2 = pdc = ""
    iac1 = iac2 = iac3 = energy_today = total_energy = temp = fault = temp_ipm = ""

    count = 0
    # Get Parameters. If there are 0 parameters, then report an error
    # Otherwise accept the line. Note that add 1 to the register values, since they all start with '1' not '0'	
    # DO NOT use the '-0' modpoll command argument. If its set, it will be impossible to collect register 0 value
    if "1" in register_dict:
        status = register_dict["1"]
        if (status in status_dict):
            status = status_dict[status]
        count += 1

    if "41" in register_dict:
        fault = register_dict["41"]
        count += 1
        result, fault_int = convert_to_int(fault)
        if (result):
            if (fault_int < 24 and fault_int > 0):
                fault = "Error: 99+x"
            elif (fault_int > 23):
                if str(fault_int) in fault_dict:
                    fault = fault_dict[str(fault_int)]
                else:
                    fault = str(fault_int)

	if (("27" in register_dict) and (("28" in register_dict))):
		num2 = register_dict["28"]
		num1 = register_dict["27"]
		result, value = convert_32(num1, num2)
		if (result):
			result, energy_today = convert_to_float(value)
			if (result):
				energy_today = energy_today / 10
				count += 1

	if (("29" in register_dict) and (("30" in register_dict))):
		num2 = register_dict["30"]
		num1 = register_dict["29"]
		result, value = convert_32(num1, num2)
		if (result):
			result, total_energy = convert_to_float(value)
			if (result):
				total_energy = total_energy / 10
				count += 1

	if "33" in register_dict:
		temp_raw = register_dict["33"]
		result, temp = convert_to_float(temp_raw)
		if (result):
			temp = temp / 10 # Divide by 10
			count += 1

	if "42" in register_dict:
		temp_ipm_raw = register_dict["42"]
		result, temp_ipm = convert_to_float(temp_ipm_raw)
		if (result):
			temp_ipm = temp_ipm / 10 # Divide by 10
			count += 1

	if "14" in register_dict:
		freq_raw = register_dict["14"]
		result, freq = convert_to_float(freq_raw)
		if (result):
			freq = freq / 100 # Divide by 100
			count += 1

	if "4" in register_dict:
		vdc1_raw = register_dict["4"]
		result, vdc1 = convert_to_float(vdc1_raw)
		if (result):
			vdc1 = vdc1 / 10 # Divide by 10
			count += 1

	if "5" in register_dict:
		idc1_raw = register_dict["5"]
		result, idc1 = convert_to_float(idc1_raw)
		if (result):
			idc1 = idc1 / 10 # Divide by 10
			count += 1

	if "8" in register_dict:
		vdc2_raw = register_dict["8"]
		result, vdc2 = convert_to_float(vdc2_raw)
		if (result):
			vdc2 = vdc2 / 10 # Divide by 10
			count += 1

	if "9" in register_dict:
		idc2_raw = register_dict["9"]
		result, idc2 = convert_to_float(idc2_raw)
		if (result):
			idc2 = idc2 / 10 # Divide by 10
			count += 1

	if (("12" in register_dict) and (("13" in register_dict))):
		num2 = register_dict["13"]
		num1 = register_dict["12"]
		result, value = convert_32(num1, num2)
		if (result):
			result, pac = convert_to_float(value)
			if (result):
				pac = pac / 10 # Divide by 10
				count += 1

	if "15" in register_dict:
		vac1_raw = register_dict["15"]
		result, vac1 = convert_to_float(vac1_raw)
		if (result):
			vac1 = vac1 / 10 # Divide by 10
			count += 1

	if "19" in register_dict:
		vac2_raw = register_dict["19"]
		result, vac2 = convert_to_float(vac2_raw)
		if (result):
			vac2 = vac2 / 10 # Divide by 10
			count += 1

	if "23" in register_dict:
		vac3_raw = register_dict["23"]
		result, vac3 = convert_to_float(vac3_raw)
		if (result):
			vac3 = vac3 / 10 # Divide by 10
			count += 1

	if "16" in register_dict:
		iac1_raw = register_dict["16"]
		result, iac1 = convert_to_float(iac1_raw)
		if (result):
			iac1 = iac1 / 10 # Divide by 10
			count += 1

	if "20" in register_dict:
		iac2_raw = register_dict["20"]
		result, iac2 = convert_to_float(iac2_raw)
		if (result):
			iac2 = iac2 / 10 # Divide by 10
			count += 1

	if "24" in register_dict:
		iac3_raw = register_dict["24"]
		result, iac3 = convert_to_float(iac3_raw)
		if (result):
			iac3 = iac3 / 10 # Divide by 10
			count += 1

	if (("6" in register_dict) and (("7" in register_dict))):
		num2 = register_dict["7"]
		num1 = register_dict["6"]
		result, value = convert_32(num1, num2)
		if (result):
			result, pdc1 = convert_to_float(value)
			if (result):
				pdc1 = pdc1 / 10
				count += 1

	if (("10" in register_dict) and (("11" in register_dict))):
		num2 = register_dict["11"]
		num1 = register_dict["10"]
		result, value = convert_32(num1, num2)
		if (result):
			result, pdc2 = convert_to_float(value)
			if (result):
				pdc2 = pdc2 / 10
				count += 1

	if (("2" in register_dict) and (("3" in register_dict))):
		num2 = register_dict["3"]
		num1 = register_dict["2"]
		result, value = convert_32(num1, num2)
		if (result):
			result, pdc = convert_to_float(value)
			if (result):
				pdc = pdc / 10 
				count += 1

    if (count < 1):
        if (debug > 0):
            print("Errors were encountered")
        errors = True
        return (errors, " ", " ")


    if (debug > 0):
        print "For inverter at address: ", rtu_address
        print "\tStatus: ", status
        print "\tDC Voltage 1 (V): ", vdc1
        print "\tDC Current 1 (A): ", idc1
        print "\tDC Power 1 (W): ", pdc1
        print "\tDC Voltage 2 (V): ", vdc2
        print "\tDC Current 2 (A): ", idc2
        print "\tDC Power 2 (W): ", pdc2
        print "\tDC Power (W): ", pdc
        print "\tAC Power (W): ", pac
        print "\tGrid Frequency (Hz): ", freq
        print "\tAC Voltage 1 (V): ", vac1
        print "\tAC Voltage 2 (V): ", vac2
        print "\tAC Voltage 3 (V): ", vac3
        print "\tAC Current 1 (A): ", iac1
        print "\tAC Current 2 (A): ", iac2
        print "\tAC Current 3 (A): ", iac3
        print "\tEnergy today (kWh): ", energy_today 
        print "\tTotal Energy (kWh): ", total_energy 
        print "\tInverter Temperature (C): ", temp
        print "\tIPM Temperature (C): ", temp_ipm
        print "\tFault: ", fault

    datetime_str = get_datetime()


    header = "# Datetime, Status, DC Voltage 1 (V), DC Current 1 (A), DC Power 1 (W), DC Voltage 2 (V), DC Current 2 (A), DC Power 2 (W), DC Power (W), AC Power (W), Grid Frequency (Hz), AC Voltage 1 (V), AC Voltage 2 (V), AC Voltage 3 (V), AC Current 1 (A), AC Current 2 (A), AC Current 3 (A), Energy today (kWh), Total Energy (kWh), Inverter Temperature (C), IPM Temperature (C), Fault\n"

    output_str =  datetime_str + "," +  str(status) + "," + str(vdc1) + "," + str(idc1) + "," + str(pdc1) + "," + str(vdc2) + "," + str(idc2) + "," + str(pdc2) + "," + str(pdc) + "," + str(pac) + "," + str(freq) + "," + str(vac1) + "," + str(vac2) + "," + str(vac3) + "," + str(iac1) + "," + str(iac2) + "," + str(iac3) + "," + str(energy_today) + "," + str(total_energy) + "," + str(temp) + "," + str(temp_ipm)  + "," + str(fault) +  "\n"

	# return the header and output
    return (errors, header, output_str)


# This function converts 2 binary 16 bit numbers to a 32 bit signed integer
def convert_32(num1_str, num2_str):
	try:
		# Handle any numbers are -vxe
		num1_int = int(num1_str)
		max_int16 = pow(2,16)
		if (num1_int < 0):
			num1_int = max_int16 + num1_int
		
		num2_int = int(num2_str)
		max_int16 = pow(2,16)
		if (num2_int < 0):
			num2_int = max_int16 + num2_int

		num1_bin = bin(num1_int)[2:]
		num2_bin = bin(num2_int)[2:]
		# if any numbers are 

		res = num1_bin + num2_bin
		number = int(res, 2)
		full_int = pow(2,32)
		if (number > (full_int/2)):
			number = number - full_int
		return True, number
	except:
		return False, ""

#~~~~~~~~~~~~~~~~~~~   END Functions ~~~~~~~~~~~~~~~~~~~~~~~

# Check script is run as root
if os.geteuid() != 0:
	print "You need to have root privileges to run this script, or as \'sudo\'. Exiting."
	sys.exit(1)

#check the arguments
arguments = check_args(7)
if (len(arguments) < 7):
	print "The arguments cannot be empty. Usage: ", USAGE
	sys.exit(2)

device = arguments[1]
port_str = arguments[2]
start_address = arguments[3]
end_address = arguments[4]
log_directory = arguments[5]
query_type = arguments[6] 
debug_str = arguments[7]

# Convert debug
retval, debug = convert_to_int(debug_str)
if (not retval):
	print "Debug needs to be an integer number. Value entered: ",debug_str
	sys.exit(3)

# If the logging directory doesn't exist, create it
if (not os.path.exists(log_directory)):
	os.makedirs(log_directory)

# Check that no other scripts are running
pidfile = PIDFILE + device + ".pid"
pidfile = os.path.join(log_directory, pidfile)
if check_pidfile(pidfile, debug):
	print "This script is already running"
	sys.exit(4)

# If any args are empty, exit with error
if ((not device) or (not start_address) or (not end_address) or (not log_directory)  or (not query_type)):
	print "The arguments cannot be empty. Usage: ", USAGE
	sys.exit(5)

# Convert start and stop addresses
retval_start, start_addr = convert_to_int(start_address)
retval_end, end_addr = convert_to_int(end_address)
if ((not retval_start) or (not retval_end)):
	print "Start and End Addresses need to be an integers"
	sys.exit(6)

# Convert port
retval, port = convert_to_int(port_str)
if (not retval):
	print "Port needs to be an integer number. Value entered: ", port_str
	sys.exit(7)

# Convert query_type
if ((query_type != "ENC") and (query_type != "RTU")):
	print "Query type must be either ENC or RTU. Value entered: ", query_type
	sys.exit(7)


start_time = time.time()

tcp_enc = False
# First get the inverter parameter data
if (query_type == "ENC"):
	tcp_enc = True

# For inverters, do the following
for rtu_address in range(start_addr, (end_addr + 1)):
	attempts = 7
	while (attempts > 0):
		time.sleep(2) # ... wait between reads, as recommended by the documentation
		# NB: device will be an IP address
		(errors, header_line, inverter_line) = read_inverter(device, tcp_enc, device, str(rtu_address), str(port), debug)
		if (not errors):
			# Write the log entry, as a date entry in the log directory
			date_str = (time.strftime("%d-%b-%Y"))
			log_filename = date_str + ".csv"
			name = "inverter_" + str(device) + "_" + str(rtu_address)
			log_directory_inv = os.path.join(log_directory, name)
			write_log(log_directory_inv, log_filename, header_line, inverter_line, debug, True, log_directory_inv, "latest.csv")
			break;
		else:
			attempts = attempts -1


elapsed_time = time.time() - start_time
if (debug > 0):
	print "This request took: ",elapsed_time, " seconds."

# Remove the PID file	
if os.path.isfile(pidfile):
	os.unlink(pidfile)

print 0

