#!/bin/bash
source ./.env.shell.local
screenname=$PROD_SCREEN_NAME
if [ "$app" = 'dev' ]; then
	echo dev
	screenname=$DEV_SCREEN_NAME
fi
echo "screenname = $screenname app = $app"
screen -S $screenname -d -m
if [ "$app" = 'dev' ]; then
	screen -S $screenname -X -p0 stuff $'sh dev_run_bot.sh\n'
else
	screen -S $screenname -X -p0 stuff $'sh run_bot.sh\n'
fi
#screen -S $screenname -X screen -t "parser run"
#if [ "$app" = 'dev' ]; then
#	screen -S $screenname -X -p1 stuff $'sh dev_run_parser.sh\n'
#else
#	screen -S $screenname -X -p1 stuff $'sh run_parser.sh\n'
#fi
