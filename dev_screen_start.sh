#!/bin/bash
screen -S botdev -d -m
screen -S botdev -X -p0 stuff $'sh dev_run_bot.sh\n'
screen -S botdev -X screen -t "parser run"
screen -S botdev -X -p1 stuff $'sh dev_run_parser.sh\n'
