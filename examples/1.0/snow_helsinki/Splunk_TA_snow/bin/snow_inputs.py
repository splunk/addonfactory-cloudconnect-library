#!/usr/bin/python
"""
This is the main entry point for My TA
"""
import re
import os

ta_name = os.path.basename(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ta_lib_name = re.sub("[^\w]+", "_", ta_name.lower())
__import__(ta_lib_name + "_import_declare")

import cloudconnectlib.splunktacollectorlib.cloud_connect_mod_input as mod_input

def ta_run():
    mod_input.run()

if __name__ == "__main__":
    ta_run()
