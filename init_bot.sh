#!/bin/bash
secret_file="./.env.secret.local"
shared_file="./.env.shared.local"
shell_file="./.env.shell.local"

read -p "Enter token: " token
read -p "Enter url: " url
read -p "Enter name: " name
read -p "Enter bot owner telegram id: " bot_owner
read -p "Enter screen name prod: " screen_name_prod
read -p "Enter screen name dev: " screen_name_dev
echo "url: $url"
echo "name: $name"
echo "token: $token"
echo "screen name prod: $screen_name_prod"
echo "screen name dev: $screen_name_dev"
read -p "Continue? (Y/N): " confirm && [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]] || exit 1
if [ ! -f "$secret_file" ]
then
	cp ./.env.secret "$secret_file"
fi
if [ "" != "$token" ]; then
	sed "s/BOT_TOKEN=.*/BOT_TOKEN=${token}/g" "$secret_file"
fi

if [ ! -f "$shared_file" ]
then
	cp ./.env.shared "$shared_file"
fi
if [ "" != "$url" ]; then
	sed -e "s@\(URL\|BUTTON_URL\)=.*@\1=${url}@g" "$shared_file"
fi
if [ "" != "$name" ]; then
	sed -e "s@\(SIZO_NAME=\).*@\1${name}@g" "$shared_file"
fi
if [ "" != "$bot_owner" ]; then
	sed -e "s@\(BOTOWNER_ID=\).*@\1${bot_owner}@g" "$shared_file"
fi

if [ ! -f "$shell_file" ]
then
	cp ./.env.shell "$shell_file"
fi
if [ "" != "$screen_name_prod" ]; then
	sed -e "s@\(PROD_SCREEN_NAME=\).*@\1${screen_name_prod}@g" "$shell_file"
fi
if [ "" != "$screen_name_dev" ]; then
	sed -e "s@\(DEV_SCREEN_NAME=\).*@\1${screen_name_dev}@g" "$shell_file"
fi
