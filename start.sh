#!/bin/bash

# Sync system clock
ntpdate -s time.nist.gov

python main.py
