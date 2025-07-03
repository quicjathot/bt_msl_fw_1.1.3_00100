#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0
#
# Convert WHENCE to YAML format
#

from pylib.whence import Whence

whence = Whence()
whence.load_whence("WHENCE")
whence.save_yaml("WHENCE.yaml", remove_empty=True)
print("WHENCE data converted to YAML and saved to WHENCE.yaml")
