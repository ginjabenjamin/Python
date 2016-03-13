# SSID Metrics

Python script to collate and parse PineAP log files. Output is written
to a tab-delimited data file. Data file is additive and stores only 
unique values. Log contains:

	MAC - Hashed MAC address
	Event - Captured event type (Probe, Association)
	SSID - ESSID name of the Wireless AP
	Maker - Device manufacturer, based on OUI lookup

Metrics option displays the most common SSIDs, most common device 
manufacturers, and the average number of SSIDs per device.

