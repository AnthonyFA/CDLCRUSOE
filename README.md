## Quickstart


To start building the environment to run CRUSOE:
``` shell
docker compose build --no-cache
docker compose up 
```
Once the scenario is launched it will be necessary to check if the Neo4j Database is active, so we must access the observer container and see if it is running:
``` shell
docker exec -it "ID"  /bin/bash
neo4j status
```
In case it does not run we will have to launch `neo4j start`.
Once it finishes running, access the link where CRUSOE is displayed, and enter the values **neo4j:neo4j** as user:password, after entering them we will be able to change the password. In this case we recommend to enter the password
password because it is the one that allows the correct operation.

To be able to load the data and test the environment, we recommend to load the .dump through the .sh that we provide (this is loaded locally so it should not give problems).
``` shell
./neo4jadmin-dumo_database.sh 
```

## Modifications
The modifications made to put in operation the original CRUSOE has been the adaptation of neo4j in the file **crusoe_observer/Dockerfile**, where the version `neo4j=1:4.4.41` and `stable 4.4` have been added so that this will have a more updated version. In addition, a number of plugins have been added to make them work:
```
COPY ansible/roles/neo4j/files/apoc-4.4.0.35-all.jar /var/lib/neo4j/plugins/
COPY ansible/roles/neo4j/files/neo4j-graph-data-science-2.3.0.jar /var/lib/neo4j/plugins/
```

Another modified element in this project has been the IPs shown throughout the **docker-compose.yml**, where we have set the IP of the local machine we have worked with throughout our research project. So if you want to deploy it on your own, we recommend that you use a local or respective network to set up the scenario.
