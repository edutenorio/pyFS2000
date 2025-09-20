import logging
from icecream import ic
import numpy as np
import os
from pyFS2000 import Model, set_logger


set_logger(logger_name='FS2000', level=logging.DEBUG, log_file='load_tests.log')

m1 = Model()
m1.load_active()
ic(m1)

for lc in m1.LoadCaseList:
    print(lc)
    print(lc.summary_str())
    print("\n\n")

for lcomb in m1.LoadCombinationList:
    print(lcomb)
    print(lcomb.summary_str())
    print("\n\n")