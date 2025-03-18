## Quickstart

Para empezar a construir el entorno basta con lanzar:
``` shell
Docker compose build --no-cache
Docker compose up 
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
