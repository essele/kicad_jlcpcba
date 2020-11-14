#!/usr/bin/python

import sys
import os
import re

BOM = {}
REFDB = {}

def init():
    global BOM
    global REFDB
    BOM = {}
    REFDB = {}

#
# Reads the schematic, but takes a "sheetpath" so that we can properly
# track nested sheets (False the first time around)
#
def read_sch(schfile, spath=""):
    fh = open(schfile, "r")

    # Dictionary to store the stuff we find...
    item = {}

    # Flags
    gotonext = False
    insheet = False

    # Now iterate through the lines in the file...
    for line in fh:
        line = line.rstrip()

        # If we have a sub-sheet then we need to find the filename
        if (re.match('^\$Sheet', line)):
            insheet = True
            item = {}
            continue

        if (insheet):
            #
            # Get the sheet uid...
            #
            m = re.match('^U ([^\s]+)', line)
            if (m):
                item['uid'] = m.group(1)

            m = re.match('^F1 "([^"]+)".*', line)
            if (m):
                d = os.path.dirname(schfile)
                p = d + "/" + m.group(1)
                sp = spath + "/" + item['uid']
                read_sch(p, sp)
            
            if (re.match('^\$EndSheet', line)):
                insheet = False
            
            continue
    
        # Start of an item...    
        if (re.match('^\$Comp$', line)):
            item = {}
            continue

        # We care about all units...
        m = re.match('^U (\d+) (\d+) ([^\s]+)', line)
        if (m):
            item['uid'] = m.group(3)
            gotonext = False
            continue

        # We only get past here if we are processing a unit 1 item
        if (gotonext):
            continue

        # New approach to finding a reference:
        #
        # If we are not in a subsheet (no spath) then we just use "F 0".
        #
        # If we are in a subsheet (have spath) then we see if we have a matching
        # AR Path, otherwise we fall back to using "F 0", this caters for the
        # situation where a subsheet is only used once and has no AR Path.
        if (spath):
            # The AR Path version...
            m = re.match('^AR Path="([^"]+)" Ref="([^"]+)".*', line)
            if (m):
                if (m.group(1).startswith(spath)):
                    item['reference'] = m.group(2)
                    item['uid'] = m.group(1)
                continue

        if (not "reference" in item):
            # The normal version... if we haven't already matched
            m = re.match('^F 0 "([^"]+)"', line)
            if (m):
                item['reference'] = m.group(1)
                continue

        # Pull out the value...
        m = re.match('^F 1 "([^"]+)"', line)
        if (m):
            item['value'] = m.group(1)
            continue

        # Pull out the footprint...
        m = re.match('^F 2 "([^"]+)"', line)
        if (m):
            item['footprint'] = m.group(1)
            continue

        # Pull out the LCSC part number...
        m = re.match('^F \d+ "([^"]+)" .* "LCSC"$', line)
        if (m):
            item['lcsc'] = m.group(1)
            continue

        # Store it if it looks ok at the end
        if (re.match('^\$EndComp$', line)):
            if (not "footprint" in item):
                continue

            if (not "lcsc" in item):
                item['lcsc'] = ""

            uid = item['uid']

            if (uid[0] == '/'):
                uid = uid[1:]
    
            # Store the item in the reference DB
            REFDB[uid.lower()] = item

            # Build a key for BOM uniqing...
            key = item['value'] + "//" + item['footprint'] + "//" + item['lcsc']

            # Make sure we have a set ready to receive the references
            if (not key in BOM):
                BOM[key] = set()

            # Update the BOM with the reference we've found... (uniq)
            BOM[key].add(item['reference'])


def output(outfile=False):
    if (outfile):
        fh = open(outfile, "w")
    else:
        fh = sys.stdout
    
    fh.write("Comment,Designator,Footprint,LCSC\n")

    for k in BOM.keys():
        (value, footprint, lcsc) = re.split("//", k)
        refs = ",".join(BOM[k])
        fh.write('"'+value+'","'+refs+'","'+footprint+'","'+lcsc+'"\n')

    if (outfile):
        fh.close()

