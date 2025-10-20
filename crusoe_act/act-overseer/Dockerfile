# Use an official Debian image as a base
FROM debian:10

# Correcciones de fuentes obsoletas en Debian 10
RUN sed -i 's|http://deb.debian.org/debian|http://archive.debian.org/debian|g' /etc/apt/sources.list && \
    sed -i 's|http://security.debian.org/debian-security|http://archive.debian.org/debian-security|g' /etc/apt/sources.list && \
    echo 'Acquire::Check-Valid-Until "false";' > /etc/apt/apt.conf.d/99no-check-valid-until

# Argumentos configurables
ARG VAULT_ACT_OVERSEER_PASSWORD="default_password"
ARG EXTERNAL_IP="127.0.0.1"
ARG LOCALHOST="127.0.0.1"
ARG PORT_NUMBER="8080"
ARG SERVER_NAME="crusoe.act-overseer.local"

# Instalación de Apache y dependencias Python
RUN apt-get update && \
  apt-get install -y apache2 libapache2-mod-wsgi-py3 python3-pip python2 curl && \
  a2enmod wsgi proxy proxy_http && \
  update-alternatives --install /usr/bin/python python /usr/bin/python3.7 2 && \
  update-alternatives --install /usr/bin/python python /usr/bin/python2 1 && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

# Copiar código fuente del act-overseer
COPY . /tmp/act-overseer

RUN pip3 install django-cors-headers

# Instalar dependencias Python del act-overseer
RUN pip3 install --no-cache-dir --force-reinstall /tmp/act-overseer

# Copiar configuración personalizada del sitio Apache
COPY ./docker-config/act_overseer.conf /etc/apache2/sites-available/

# Personalizar configuración según argumentos
RUN sed -i \
  -e "s/{{ portnumber }}/$PORT_NUMBER/" \
  -e "s/{{ server_name }}/$SERVER_NAME/" \
  /etc/apache2/sites-available/act_overseer.conf

# Habilitar el sitio y configurar Apache para escuchar el puerto deseado
RUN a2ensite act_overseer.conf && \
    echo "Listen $PORT_NUMBER" >> /etc/apache2/ports.conf

# Configurar ProxyPass directo en el sitio por defecto (por seguridad)
RUN sed -i "/<\/VirtualHost>/i \\\tProxyPass /act http://${LOCALHOST}:${PORT_NUMBER}/act\n\tProxyPassReverse /act http://${LOCALHOST}:${PORT_NUMBER}/act" /etc/apache2/sites-available/000-default.conf

# Configuración del archivo act_overseer_config con credenciales y URL
RUN sed -i 's/"user",/"crusoe",/' /usr/local/lib/python3.7/dist-packages/act_overseer/data/act_overseer_config && \
    sed -i 's/"pass",/"'"$VAULT_ACT_OVERSEER_PASSWORD"'",/' /usr/local/lib/python3.7/dist-packages/act_overseer/data/act_overseer_config && \
    sed -i 's|"https://crusoe.csirt.muni.cz"|"'"$EXTERNAL_IP"'"|' /usr/local/lib/python3.7/dist-packages/act_overseer/data/act_overseer_config

RUN mkdir -p /var/log/crusoe && \
  touch /var/log/crusoe/act_overseer_rest_api.log /var/log/crusoe/act_decide_to_act.log && \
  chmod 0666 /var/log/crusoe/*.log && \
  cp -r /tmp/act-overseer/act_overseer_rest_api /var/www/ && \
  chown -R www-data:www-data /var/www/act_overseer_rest_api


# Instalar dependencias del componente DECIDE (Neo4j, Mulval, etc.)
RUN pip3 install neo4j-driver==5.0 pytest neo4j

COPY ./docker-config/neo4j-client /tmp/neo4j-client
RUN pip3 install --no-cache-dir --force-reinstall /tmp/neo4j-client

# Variables de entorno para MULVAL y XSB
ENV MULVALROOT=/opt/mulval
ENV XSBROOT=/opt/XSB
ENV PATH="$PATH:$MULVALROOT/bin:$MULVALROOT/utils:$XSBROOT/bin:$XSBROOT/build"

# Paquetes adicionales y compilación de XSB y MULVAL
RUN apt-get update && apt-get install -y \
  python3.7 python2 python3-pip default-jdk build-essential \
  bison flex ca-certificates-java autoconf automake libtool gcc make

# Preparar directorios
RUN mkdir -p /usr/share/man/man1

# Descargar y descomprimir MULVAL
ADD https://people.cs.ksu.edu/~xou/argus/software/mulval/mulval_1_1.tar.gz /opt/mulval_1_1.tar.gz
RUN tar -xzvf /opt/mulval_1_1.tar.gz -C /opt/

# Descargar y descomprimir XSB
ADD http://xsb.sourceforge.net/downloads/XSB.tar.gz /opt/XSB.tar.gz
RUN tar -xzvf /opt/XSB.tar.gz -C /opt/

# Sustituir scripts de configuración de XSB
COPY ./docker-config/config.sub /opt/XSB/build/
COPY ./docker-config/config.guess /opt/XSB/build/

# Compilar XSB
RUN cd /opt/XSB/build && \
  ./configure && \
  ./makexsb

# Configurar y compilar MULVAL
RUN sed -i 's|^LIBS=.*$|LIBS=/opt/mulval/lib/dom4j-1.6.1.jar:/opt/mulval/lib/jaxen-1.1.1.jar:/opt/mulval/lib/mysql-connector-java-5.1.8-bin.jar|' \
    /opt/mulval/src/adapter/Makefile
RUN cd /opt/mulval && make

# Instalar dependencias de compilación para numpy/scipy/scikit-learn
RUN apt-get update && apt-get install -y \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    pkg-config

# Actualizar pip, wheel y setuptools para mejorar compatibilidad
RUN pip3 install --upgrade pip setuptools wheel

# Instalar numpy, scipy y scikit-learn en versiones compatibles con Python 3.7
RUN pip3 install "numpy<1.22" "scipy<1.8" "scikit-learn<1.1"

# Copiar requirements.txt de crusoe_decide
COPY ./docker-config/crusoe_decide/requirements.txt /tmp/crusoe_decide/requirements.txt

RUN pip3 install -r /tmp/crusoe_decide/requirements.txt

COPY ./docker-config/crusoe_decide/ /tmp/crusoe_decide


RUN if [ -f /tmp/crusoe_decide/requirements.txt ]; then \
      pip3 install -r /tmp/crusoe_decide/requirements.txt; \
    fi

RUN pip3 install --no-cache-dir --force-reinstall /tmp/crusoe_decide

CMD ["apachectl", "-D", "FOREGROUND"]
