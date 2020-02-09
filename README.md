# kicad_jlcpcba
KiCad pluging to create BOM and Placement files for JLCPCB's PCBA service

This is a very simple plugin that builds the required BOM and Placement files for the JLCPCBA assembly service.

It works by reading in the schematic to build up the LCSC part numbers, and then matching with the components that are on the pcb.

Custom rotations (needed to ensure components end up the right orientation for the service) are contained in rotations.cf and are read each time the action is run, so you can edit as needed and retry until everything is good.

Please feedback any changed needed to the rotations.

INSTALL

To install simply git clone into your plugins directory.

USAGE

Simply ensure that any components you want placed by the JLC service have an extra attribute in the schematic called "LCSC", and the value should be the LCSC part number, this is used to pull part number details out.

The from within the pcb editor you can click on the JLCPCB action button (or use the external plugins menu) to run the action.

This will generate three files in the project directory:

| Filename | Description |
| --- | --- |
| projectname_bom.csv | the BOM file |
| projectname_top_pos.csv | the placement file for the top of the board |
| lprojectname_bottom_pos.csv | the placement file for the bottom of the board |

These files can be uploaded to the JLCPCB PCBA page when requested (you will need to choose either top or bottom), if the rotations are not correct then you can edit rotations.cf and recreate/reupload the files.

TODO

Still todo:

- More error checking
- More detailed instructions with pictures

