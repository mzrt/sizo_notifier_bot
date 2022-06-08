#!/bin/bash
source ./.env.shell.local
screenname=$PROD_SCREEN_NAME
if [ "$app" = 'dev' ]; then
	echo dev
	screenname=$DEV_SCREEN_NAME
fi
echo "screenname = $screenname, app = $app"

screen -S $screenname -X quit
#screen -S botdev -X kill
