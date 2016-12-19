#!/usr/bin/python
"""
This is the main entry point for My TA
"""
import os
import re

ta_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ta_lib_name = re.sub("[^\w]+", "_", ta_name.lower())
__import__(ta_lib_name + "_import_declare")

import cloudconnectlib.splunktacollectorlib.cloud_connect_mod_input as mod_input

if __name__ == "__main__":
    mod_input.run()
