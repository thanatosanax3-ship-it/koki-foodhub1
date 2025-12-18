#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Remove UTF-8 BOM from template file"""
import os

file_path = 'core/templates/pages/product_list.html'

# Read the file in binary mode
with open(file_path, 'rb') as f:
    content = f.read()

# Check for UTF-8 BOM (EF BB BF)
if content.startswith(b'\xef\xbb\xbf'):
    print("UTF-8 BOM found! Removing...")
    # Remove BOM
    content = content[3:]
    # Write back without BOM
    with open(file_path, 'wb') as f:
        f.write(content)
    print("BOM removed successfully!")
else:
    print("No BOM found in file")
