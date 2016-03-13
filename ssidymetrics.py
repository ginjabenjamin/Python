#!/usr/bin/env python
'''
Reads PineAP log file and outputs tab-delimited file 
and optionally displays metrics
'''
__author__ = "Benjamin"
__copyright__ = "Copyright 2016, Hivemind"
__license__ = "GPL"
__version__ = "1.0"

import argparse
import hashlib
import os
import sqlite3
import urllib2

db = sqlite3.connect(':memory:')
ouiFilename = 'oui.txt'

# Setup the database table
def init_database():
    db.text_factory = sqlite3.OptimizedUnicode
    cur = db.cursor()
    cur.execute('create table ssid(mac text, event text, ssid text, maker text)')
    return cur

# If the OUI file is not present, download it
def get_oui():
    url = 'http://standards-oui.ieee.org/oui.txt'
    u = urllib2.urlopen(url)
    f = open(ouiFilename, 'w')
    meta = u.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    file_size_dl = 0
    block_sz = 8192

    while True:
        buffer = u.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        f.write(buffer)
        status = "[+] Downloading %s: %s / %s %3.2f%%" % (
            url, file_size_dl, file_size, file_size_dl * 100. / file_size)
        status = status + chr(8) * (len(status) + 1)
        
        # No carriage-return so we update the line
        print status,

    f.close()

# Convert PineAP log to SsidyMetrics
def parse_pineap(logFilename, cur, oui):
    # print("[+] Parsing PineAP log '%s'" % logFilename)
    count  = 0
    
    if(not os.path.isfile(logFilename)):
        print("[-] Log file not found: '%s'" % logFilename)
        return
    
    logFile = open(logFilename, 'r')
    ssidList = []
        
    # Process the PineAP log
    for ssid in logFile:
        count += 1
        
        try:
            # No idea why there are returns in our SSIDs...
            date, event, mac, ssid = ssid.strip('\r').split(',\t')
        except ValueError:
            if(len(ssid.strip('\n')) > 1):
                print('BAD RECORD (%d): %s' % (count, ssid))
            continue
    
        # Hash the MAC address so that can identify same sources without publishing
        # the actual MAC addresses
        macHash = hashlib.sha1(mac).hexdigest()
    
        # Check for the device's manufacturer
        if(mac[:8] in oui.keys()):
            maker = oui[mac[:8]]
        else:
            maker = '(Unknown)'

        ssidList.append((macHash, event, ssid.strip('\n'), maker))
    
    # Add SSIDs to table
    cur.executemany('insert into ssid(mac, event, ssid, maker) values(?,?,?,?)', ssidList)
    print("[+] Read %d records from '%s'" % (cur.rowcount, logFilename))
    db.commit()
    
    logFile.close()
    
# Read existing data file
def parse_data(dataFilename, cur):
    # print("[+] Reading data from '%s'" % dataFilename)
    if(not os.path.isfile(dataFilename)):
        print("[-] Data file not found: '%s'" % dataFilename)
        return
    
    dataFile = open(dataFilename, 'r')
    ssidList = []
        
    # Process the PineAP log
    for ssid in dataFile:
        # Skip the header row
        if(ssid == 'Mac\tEvent\tSsid\tMaker\n'):
            continue
        
        mac, event, ssid, maker = ssid.split('\t')    
        ssidList.append((mac, event, ssid, maker.strip('\n')))
    
    # Add SSIDs to table
    cur.executemany('insert into ssid(mac, event, ssid, maker) values(?,?,?,?)', ssidList)
    print("[+] Read %d records from '%s'" % (cur.rowcount, dataFilename))
    db.commit()
    
    dataFile.close()

def query(operation, limit, cur):
    if(operation == 'count'):
        count = 0
        for record in cur.execute('select distinct * from ssid'):
            count += 1
        print('[+] Data contains %d unique records' % count)
    elif(operation == 'metric'):
        if(limit > 0):
            sqlLimit = (' limit %d' % limit)
        else:
            sqlLimit = ''

        # Top SSIDs 
        print('\nTop SSIDs' + ' '*24 + 'Count')
        print('-'*32 + ' ' + '--------')
        query = 'select ssid, count(distinct mac) xCount '
        query += 'from ssid group by ssid '
        query += 'order by xCount desc' + sqlLimit
 
        for row in cur.execute(query):
            ssid = row[0].strip('\r')
            count = str(row[1])
            count = ' '*(8 - len(count)) + count
            print(ssid[:32] + ' '*(32 - len(ssid)) + count)        

        # Top Device Manufacturers 
        print('\nTop Manufacturers' + ' '*16 + 'Count')
        print('-'*32 + ' ' + '--------')
        query = 'select maker, count(distinct mac) xCount '
        query += 'from ssid group by maker '
        query += 'order by xCount desc' + sqlLimit
 
        for row in cur.execute(query):
            maker = row[0].strip('\r')
            count = str(row[1])
            count = ' '*(8 - len(count)) + count
            print(maker[:32] + ' '*(32 - len(maker)) + count)        

        # Average SSIDs 
        print('\nAverage SSIDs per Device')
        print('------------------------')
        query = 'select avg(xcount) xCount '
        query += 'from (select mac, count(distinct ssid) xcount '
        query += 'from ssid group by mac) '
        query += 'order by xCount desc'

        for row in cur.execute(query):
            print(row[0])



# Process the OUI file
def parse_oui():
    manufacturer = dict()
    # Check if we have the OUI file
    if(os.path.isfile(ouiFilename)):
        print('[+] Using existing oui.txt')
        # ouiFile = open("/root/Dev/git/SsidyMetrics/oui.txt", "r")
    else:
        print('[+] Retrieving oui.txt from IEEE')
        get_oui()

    ouiFile = open(ouiFilename, 'r')

    for oui in ouiFile:
        # We only want the hex notation
        if '(hex)' in oui:
            # Break into pieces
            ouiHex, sep, maker = oui.strip().partition('(hex)')
    
            # Make MAC lowercase and change hyphens to colons,
            # and Remove leading tabs from Company names
            manufacturer[ouiHex.strip().replace('-', ':').lower()] = maker.strip('\t')    
    
    ouiFile.close()
    
    print("[+] Populated manufacturer OUI list (%d)" % len(manufacturer))
    
    return manufacturer

# Output the unique MAC/SSID combinations

def write_data(dataFilename, cur):
    count = 0

    print("[+] Writing data file '%s'" % dataFilename)
    dataFile = open(dataFilename, 'w')

    dataFile.write('Mac\tEvent\tSsid\tMaker\n')

    for row in cur.execute('select distinct * from ssid'):
        dataFile.write(row[0] + '\t' + row[1] + '\t' + row[2].strip('\r') + '\t' + row[3] + '\n')
        count += 1
    
    print("[+] Wrote %d rows" % count)

def get_parser():
    parser = argparse.ArgumentParser(description='PineAP log consolidation and metrics')
    parser.add_argument("pineaplog", nargs='*', help='PineAP log file')
    parser.add_argument('-m', '--metrics', 
        type=int,
        nargs='?',
        help='Show metrics; limit results to specified value (Zero for all)',
        const=5)
    parser.add_argument('-o', '--oui', 
        help='Do not perform device manufacturer lookup (Default: False)', 
        action='store_false')
    parser.add_argument('-t', '--test', 
        help='Parse but do not save data file  (Default: False)',
        action='store_true')
    parser.add_argument('-d', '--data', 
        type=str, 
        help='Use existing data file')
    parser.add_argument('-v', '--version',
        help='Displays the current version of SsidyMetrics',
        action='store_true')
    return parser

def main():
    parser = get_parser()
    args = vars(parser.parse_args())
    print(args)
    oui = dict()

    if args['version']:
        print('Version: %s', __version__)
        return

    if(args['data']):
        dataFilename = args['data']
    else:
        # No data specified, use default
        dataFilename = 'ssidymetrics.tab'

    if(args['metrics'] is not None or args['pineaplog']):
        cur = init_database();

        # If we are processing data, check for existing data
        parse_data(dataFilename, cur)
            
    if args['pineaplog']:
        # Parsing MACs, so check for OUI
        if args['oui']:
            # Output hex OUI's to a dictionary for lookup
            oui = parse_oui()
        else:
            print('[+] Skipping OUI lookup')

        for file in args['pineaplog']:
            parse_pineap(file, cur, oui)

        if(args['test'] == False):
            write_data(dataFilename, cur)
        else:
            query('count', 0, cur)

    if args['metrics'] is not None:
        query('metric', args['metrics'], cur)
        
    if(not args['metrics'] and not args['pineaplog'] and not args['data']):
        print('[+] No action specified. Displaying help')
        parser.print_help()

if __name__ == '__main__':
    main()
