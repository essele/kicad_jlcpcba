import pcbnew
import wx
import os
import re

class JlcpcbaPluginAction(pcbnew.ActionPlugin):
    def defaults(self):
        self.name = "Export JLCPCB PCBA Files"
        self.category = "PCBA"
        self.description = "Create BOM and CPL files for JLCPCBs PCBA Service"
        self.show_toolbar_button = True
        self.icon_file_name = os.path.join(os.path.dirname(__file__), 'jlcpcba.png')

    def Run(self):
        print("Testing")
        wx.MessageDialog(None, "Hello World").ShowModal()


