
# Purpose
Shenzhen Growatt (www.ginverter.com) supply retail and commercial grade Solar PV inverters. The purpose of this project is to collect data from Growatt Inverters and send the data to your cloud using Ardexa. Data from Growatt solar inverters is read using an RS485 connection and via the Modbus RTU protocol to the inverters and a Linux device such as a Raspberry Pi, or an X86 intel powered computer. 

## How does it work
This application is written in Python, to query Growatt inverters connected via RS485. This application will query 1 or more connected inverters at regular intervals. Data will be written to log files on disk in a directory specified by the user. Usage and command line parameters are as follows:

Usage: python growatt-ardexa.py {device} {port} {start_address} {end_address} {log_directory} {query_type} {debug_str}, where...
- {device} = it can be an IP address or something like: /dev/ttyS0
- {port} = an IP Port like 502
- {start addresses} = an RS485 start address (eg; 1-32)
- {end addresses} = an RS485 end address (eg; 1-32)
- {log directory} = the logging directory
- {query_type} = either `ENC` (which is RTU encapsulted over TCP) or `RTU`
- {debug type} = 0 (no messages, except errors), 1 (discovery messages) or 2 (all messages)
- eg: `sudo python growatt-ardexa.py /dev/ttyS0 0 1 8 /opt/ardexa RTU 1`   ... or
		`sudo python growatt-ardexa.py 192.168.1.1 502 1 8 /opt/ardexa ENC 1`

Remember these things:
1. Connection from your Linux device to the first inverter is via RS485 daisy chain.
2. Each inverter (if there are more than 1) must have a UNIQUE RS485 address

If in doubt, see the latest documentation on the Growatt website or in the `docs` directory of this project.

## How to use the script
On a raspberry Pi, or other Linux machines (arm, intel, mips or whatever), make sure Python is installed (which it should be). Then install the dependancy as follows:

```
mkdir /opt/modpoll
cd /opt/modpoll
wget http://www.modbusdriver.com/downloads/modpoll.3.4.zip
unzip modpoll.3.4.zip 
cd linux/
chmod 755 modpoll 
sudo cp modpoll /usr/local/bin
```

Then install and run this project as follows:
Note that the applications should be run as root.
```
cd
git clone https://github.com/ardexa/growatt-inverters
cd growatt-inverters
```

Usage: python growatt-ardexa.py {device} {port} {start_address} {end_address} {log_directory} {query_type} {debug_str}
eg: `sudo python growatt-ardexa.py 192.168.1.1 502 1 8 /opt/ardexa ENC 1`


## Collecting to the Ardexa cloud
Collecting to the Ardexa cloud is free for up to 3 Raspberry Pis (or equivalent). Ardexa provides free agents for ARM, Intel x86 and MIPS based processors. To collect the data to the Ardexa cloud do the following:
- Create a `RUN` scenario to schedule the Ardexa Growatt script to run at regular intervals (say every 300 seconds/5 minutes).
- Then use a `CAPTURE` scenario to collect the csv (comma separated) data from the filename (say) `/opt/ardexa/inverter1/logs/`. This file contains a header entry (as the first line) that describes the CSV elements of the file.

## Help
Contact Ardexa at support@ardexa.com, and we'll do our best efforts to help.


 

