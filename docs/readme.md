

## Documents
- Growatt - Installation and Operation Manual
- Growatt PV Inverter Modbus RS485 RTU Protocol


## Modbus Map for the GroWatt Inverters
- Uses `input registers`
- Example: modpoll -m enc -a 3 -r 1 -c 41 -t 3 -1 -p 502 192.168.1.1
- The Ardexa Plugin uses the following register values, and associated notes:

Register			Name								Notes
0					Inverter run state 			{0:"waiting", 1:"normal", 2:"fault"}
1+2				DC Power							divide by 10 to get W
3					DC Voltage 1					divide by 10 to get V
4					DC Current 1					divide by 10 to get A
5+6				DC Power 1						divide by 10 to get W
7					DC Voltage 2					divide by 10 to get V
8					DC Current 2					divide by 10 to get A
9+10				DC Power 1						divide by 10 to get W
11+12				Output Power 					divide by 10 to get W
13					Grid Frequency					divide by 100 to get Hz
14	 				AC Voltage 1					divide by 10 to get V
15					AC Current 1					divide by 10 to get A
18					AC Voltage 2					divide by 10 to get V
19					AC Current 2					divide by 10 to get A
22					AC Voltage 3					divide by 10 to get V
23					AC Current 3					divide by 10 to get A
26+27				Energy Today 					divide by 10 to get kWh
28+29				Total Energy					divide by 10 to get kWh
32					Inverter temperature			divide by 10 to get C
40					Fault Code						see notes in the Growatt documentation
41					IPM temperature				divide by 10 to get C



