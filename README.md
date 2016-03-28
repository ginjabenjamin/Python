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

usage: ssid.py [-h] [-m [METRICS]] [-o] [-t] [-d DATA] [-c CORRELATE] [-r]
               [-v]
               [pineaplog [pineaplog ...]
               
               

PineAP log consolidation and metrics

positional arguments:
pineaplog             PineAP log file(s)

optional arguments:
  -h, --help            show this help message and exit
  -m [METRICS], --metrics [METRICS]
                        Show metrics; limit results to specified value (Zero for all)
  -o, --oui             Do not perform device manufacturer lookup (Default: False)
  -t, --test            Parse but do not save data file (Default: False)
  -d DATA, --data DATA  Use existing data file
  -c CORRELATE, --correlate CORRELATE
                        Check log against data file for matching MACs
  -r, --report          Display Events by SSID and client count
  -v, --version         Displays the current version of SsidyMetrics

