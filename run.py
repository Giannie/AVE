#!/usr/bin/env python
import sys
sys.path.append("apps/mscroggs~ave")

from core import errors as e
from core.ave import AVE
import os

import buttons
buttons.init()

started = False

ave = AVE()
ave.start()

try:
    started = True
    ave.start()
except e.AVEQuit:
    ave.exit()
    print("Goodbye...")
finally:
    if started:
        ave.exit()