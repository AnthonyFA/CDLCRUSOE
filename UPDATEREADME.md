## Quickstart

Para empezar a construir el entorno basta con lanzar:
``` shell
docker compose build --no-cache
docker compose up 
```
Una vez lanzado el escenario será necesario comprobar si la Base de Datos de Neo4j esta áctiva, por lo que deberemos acceder al contenedor de observer y ver si se ejecuta:
``` shell
docker exec -it "ID"  /bin/bash
neo4j status
```
En caso de no ejecutarse deberemos lanzar `neo4j start`
Una vez se termine de ejecutar, accedemos al link en donde este desplegado CRUSOE, e introducimos los valores **neo4j:neo4j** como usuario:contraseña, tras introducirlos nos pédira cambiar la contraseña. En este caso recomendamos introducir la contraseña
password pues es la que permite el correcto funcionamiento.

Para poder cargar los datos y poner a prueba el entorno, recomendamos cargar el .dump a través del .sh que suministramos (este se carga de manera local por lo que no debería dar problemas)
``` shell
./neo4jadmin-dumo_database.sh 
```

## Modifications
Las modificaciones realizadas para poner en funcionamiento CRUSOE original ha sido la adaptación de neo4j en el archivo **crusoe_observer/Dockerfile**, en donde se ha añadido la versión `neo4j=1:4.4.41` y `stable 4.4`para que este contará con una version mas actualizada. Además, se han agregado una serie de pluggins para que estos funcionaran:
```
COPY ansible/roles/neo4j/files/apoc-4.4.0.35-all.jar /var/lib/neo4j/plugins/
COPY ansible/roles/neo4j/files/neo4j-graph-data-science-2.3.0.jar /var/lib/neo4j/plugins/
```

Otro elemento modificado en este proyecto han sido las IPs que se muestran a lo largo del **docker-compose.yml**, en donde se han establecido la IP de la máquina local con la que hemos trabajado a lo largo de nuestro proyecto de investigación. Por lo que si desea desplegarlo por su cuenta, le recomendamos que use una red local o la respectiva para montar el escenario.
