#!/bin/bash

# Sync system clock
ntpdate -s time.nist.gov

# Start the bot
python bot.py
