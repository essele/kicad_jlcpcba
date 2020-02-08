#
# Create a JLCPCB PCBA set of files to support PCBA, this requires us to
# produce a BOM file and a CPL (component placement file), which will be a
# .pos file.
#
# We do this by reading the associated schematic (mainly for part numbers)
# and then cross-matching the pcb modules.
#

import pcbnew
import os
import re

print("Hello")

#
# Setup a few useful globals...
#
global path
global name

#
# Expressions with a colon in them will be matched against
# the full footprint name (including library alias), otherwise
# it's just the short name.
#
# TODO: these need to come from a config file (ideally git updated)
#
rots = [
            ('^SOT-223',            180),
            ('^SOT-23',             180),
            ('^SOT-353',            180),
            ('^QFN-',               270),
            ('^LQFP-',              270),
            ('^TQFP-',              270),
            ('^MSOP-',              90),
            ('^TSSOP-',             270),
            ('^DFN-',               270),
            ('^SOIC-8_',            270),
            ('^VSSOP-10_-',         270),
#            ('^Lees_Footprints:',   270),
        ]

#
# Given the footprint name, work out what rotation is needed, we support
# matching against the long or short footprint names (if there is a colon
# in the regex)
#
def possible_rotate(footprint):
    fpshort = footprint.split(':')[1]

    for rot in rots:
        ex = rot[0]
        delta = rot[1]

        fp = fpshort
        if (re.search(':', ex)):
            fp = footprint

        if(re.search(ex, fp)):
            return delta

    return 0

#
# Function to read the schematic, create a grouped BOM file, and also keep
# an internal table for use by the later code
#
def create_bom(schfile):

    gotonext = False
    items = {}
    item = {}

    fh = open(schfile, "r")
    for line in fh:
        line = line.rstrip()
        print(line)

        # Start of an item...
        if (re.match('^\$Comp$', line)):
            item = {}
            continue

        # We care about unit 1...
        m = re.match('^U (\d+) (\d+) ([^\s]+)', line)
        if (m):
            if (m.group(1) != '1'):
                gotonext = True
                continue

            item['uid'] = m.group(3)
            gotonext = False
            continue

        # We only get past here if we are processing a unit 1 item
        if (gotonext):
            continue

        # Pull out the reference...
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

            items[item['uid']] = item

    fh.close()
    print("ALL ITEMS")
    print(items)

    #
    # Now we can create the BOM by grouping...
    #
    bom = []
    uniq = {}

    for i in items.values():
        key = i['value'] + "//" + i['footprint'] + "//" + i['lcsc']
        print("have key -- " + key)

        if (not key in uniq):
            uniq[key] = []

        uniq[key].append(i['reference'])

    #
    # Now output the BOM in JLCPCB format...
    #
    bomfile=path + "/" + name + "_bom.csv"
    fh = open(bomfile, "w")
    fh.write("Comment,Designator,Footprint,LCSC\n")
    for k in uniq.keys():
        (value, footprint, lcsc) = re.split("//", k)
        refs = ",".join(uniq[k])
        fh.write('"'+value+'","'+refs+'","'+footprint+'","'+lcsc+'"\n')

    fh.close()
    return items

def create():
    global path
    global name

    board = pcbnew.GetBoard()
    boardfile = board.GetFileName()
    path = os.path.dirname(boardfile)
    name = os.path.splitext(os.path.basename(boardfile))[0]
    #
    # Create the BOM and build the refdb...
    #
    refdb = create_bom(path + "/" + name + ".sch")

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
        uid = m.GetPath().replace('/', '')
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
        if (smd):
            if (layer == "B.Cu"):   # negatives for bottom layer
                y = y * -1
                fh = botfh
                lname = "bottom"

            fh.write('"' + reference + '","' + value + '","' + fpshort + '",' +
                    str(x) + ',' + str(y) + ',' + str(rot) + ',' + lname + '\n')

    topfh.close()
    botfh.close()

#create()
