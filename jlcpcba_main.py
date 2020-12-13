#
# Create a JLCPCB PCBA set of files to support PCBA, this requires us to
# produce a BOM file and a CPL (component placement file), which will be a
# .pos file.
#
# We do this by reading the associated schematic (mainly for part numbers)
# and then cross-matching the pcb modules.
#

import os
import pcbnew
import re

from . import read_sch as bom

#
# Setup a few useful globals...
#
global path
global name
global rotdb

#
# Read the rotations.cf config file so we know what rotations to apply
# later.
#
def read_rotdb(filename):
    db = []

    fh = open(filename, "r")
    for line in fh:
        line = line.rstrip()

        line = re.sub('#.*$', '', line)         # remove anything after a comment
        line = re.sub('\s*$', '', line)         # remove all trailing space

        if (line == ""):
            continue

        m = re.match('^([^\s]+)\s+(\d+)$', line)
        if m:
            db.append((m.group(1), int(m.group(2))))

        print(line)
    return db




#
# Given the footprint name, work out what rotation is needed, we support
# matching against the long or short footprint names (if there is a colon
# in the regex)
#
def possible_rotate(footprint):
    fpshort = footprint.split(':')[1]

    for rot in rotdb:
        ex = rot[0]
        delta = rot[1]

        fp = fpshort
        if (re.search(':', ex)):
            fp = footprint

        if(re.search(ex, fp)):
            return delta

    return 0

#
# Actually create the PCBA files...
#
def create_pcba():
    global path
    global name
    global rotdb

    board = pcbnew.GetBoard()
    boardfile = board.GetFileName()
    path = os.path.dirname(boardfile)
    name = os.path.splitext(os.path.basename(boardfile))[0]

    #
    # Populate the rotation db (do it here so editing and retrying is easy)
    #
    rotdb = read_rotdb(os.path.join(os.path.dirname(__file__), 'rotations.cf'))

    #
    # Create the BOM and build the refdb...
    #
    bom.init()
    bom.read_sch(path + "/" + name + ".sch")
    bom.output(path + "/" + name + "_bom.csv")
    refdb = bom.REFDB
    
    #
    # Now we can process all of the SMT elements...
    #

    # Open both layer files...
    topfile=path + "/" + name + "_top_pos.csv"
    topfh = open(topfile, "w")
    topfh.write("Designator,Val,Package,Mid X,Mid Y,Rotation,Layer\n")

    botfile=path + "/" + name + "_bottom_pos.csv"
    botfh = open(botfile, "w")
    botfh.write("Designator,Val,Package,Mid X,Mid Y,Rotation,Layer\n")

    for m in board.GetModules():
        # uid = m.GetPath().replace('/', '')
        # Need to just pull out the non-zero part at the end
        if hasattr(m.GetPath(), 'AsString'):
            uid = m.GetPath().AsString().lower()
        else:
            uid = m.GetPath().lower()

        if len(uid) == 0:
            continue

        while (uid[0] in "0/-"):
            uid = uid[1:]

        smd = ((m.GetAttributes() & pcbnew.MOD_CMS) == pcbnew.MOD_CMS)
        x = m.GetPosition().x/1000000.0
        y = m.GetPosition().y/1000000.0
        rot = m.GetOrientation()/10.0
        layer = m.GetLayerName()
        print("Got module = " + uid + " smd=" + str(smd) + " x=" + str(x) + " y=" + str(y) + " rot=" + str(rot) + "layer="+str(layer))
        print(m.GetPath() + " attr=" + str(m.GetAttributes()))

        if (not uid in refdb):
            print("WARNING: item " + uid + " missing from schematic")
            continue

        item = refdb[uid]
        reference = item['reference']
        value = item['value']
        footprint = item['footprint']

        # Now do the rotation needed...
        rot = (rot + possible_rotate(footprint)) % 360

        # Now write to the top and bottom file respectively
        fpshort = footprint.split(':')[1]
        fh = topfh
        lname = "top"
        y = y * -1                  # y is negative always???
        if (smd):
            if (layer == "B.Cu"):   
                fh = botfh
                lname = "bottom"

            fh.write('"' + reference + '","' + value + '","' + fpshort + '",' +
                    str(x) + ',' + str(y) + ',' + str(rot) + ',' + lname + '\n')

    topfh.close()
    botfh.close()

#create()
