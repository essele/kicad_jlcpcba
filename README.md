# kicad_jlcpcba
KiCad pluging to create BOM and Placement files for JLCPCB's PCBA service

This is a very simple plugin that builds the required BOM and Placement files for the JLCPCBA assembly service.

It works by reading in the schematic to build up the LCSC part numbers, and then matching with the components that are on the pcb.

Currently custom rotations are hardcoded into the script, so ideally these will need to come out.

INSTALL

To install simply git clone into your plugins directory.

TODO

Still todo:

- Separate file for custom rotations
- More error checking
- More detailed instructions

