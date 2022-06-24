#!/bin/bash
source ./.env.shell.local
source /home/user//python-virtual-environments/bot/bin/activate
screenname="SEL_$PROD_SCREEN_NAME"
echo "screenname = $screenname app = $app"
screen -S $screenname -d -m
screen -S $screenname -X screen -t "selenium run"
screen -S $screenname -X -p1 stuff $'sh run_selenium.sh\n'
