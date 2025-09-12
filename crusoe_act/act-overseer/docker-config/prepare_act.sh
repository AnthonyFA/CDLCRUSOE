#!/bin/sh
set -e

CONF_FILE="${ACT_OVERSEER_CONFIG_PATH:-/var/lib/act_overseer/act_overseer_config}"
CONF_DIR="$(dirname "$CONF_FILE")"
DEFAULT_CONF="/usr/local/lib/python3.7/dist-packages/act_overseer/data/act_overseer_config"

# Crear directorios necesarios
mkdir -p "$CONF_DIR" /var/log/crusoe

# Si no existe el fichero externo, copiar el de paquete como base
if [ ! -f "$CONF_FILE" ]; then
  cp -f "$DEFAULT_CONF" "$CONF_FILE"
fi

# Propietario y permisos adecuados para Apache/mod_wsgi (www-data)
chown -R www-data:www-data "$CONF_DIR" /var/log/crusoe
chmod 664 "$CONF_FILE"
chmod 775 "$CONF_DIR" /var/log/crusoe
