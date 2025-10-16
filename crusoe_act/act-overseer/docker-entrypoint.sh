#!/bin/sh
set -e

# Asegura directorios y permisos cuando ya está montado el volumen
mkdir -p /var/lib/act_overseer
chown -R www-data:www-data /var/lib/act_overseer

mkdir -p /var/log/crusoe
touch /var/log/crusoe/act_overseer_rest_api.log /var/log/crusoe/act_decide_to_act.log
chmod 0666 /var/log/crusoe/*.log
chown -R www-data:www-data /var/log/crusoe || true

exec apachectl -D FOREGROUND
