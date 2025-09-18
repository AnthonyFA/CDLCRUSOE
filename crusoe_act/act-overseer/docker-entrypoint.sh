#!/bin/sh
set -e

: "${ACT_OVERSEER_DATA_DIR:=/var/lib/act_overseer}"
mkdir -p "$ACT_OVERSEER_DATA_DIR"
chown -R www-data:www-data "$ACT_OVERSEER_DATA_DIR"


PKG_DIR="$(python3 -c 'import act_overseer, pathlib; print(pathlib.Path(act_overseer.__file__).parent)')"
rm -rf "$PKG_DIR/data"
ln -s "$ACT_OVERSEER_DATA_DIR" "$PKG_DIR/data"


mkdir -p /var/log/crusoe
touch /var/log/crusoe/act_overseer_rest_api.log /var/log/crusoe/act_decide_to_act.log
chown www-data:www-data /var/log/crusoe/*.log
chmod 0644 /var/log/crusoe/*.log

exec "$@"
