
services:
  crusoe_act_overseer:
    build:
      context: ./crusoe_act/act-overseer
      args:
        # Password for neo4j-rest
        VAULT_ACT_OVERSEER_PASSWORD: "password"
        # URL of neo4j-rest REST API | we are using Docker internal DNS resolving of each services
        EXTERNAL_IP: "${OBSERVE_IP}"
        # Form of localhost address - could be "localhost" or ::1, but for simplicity ipv4 loopback
        LOCALHOST: "127.0.0.1"
        # Port on which act will start - we will then use apache2 proxy to proxy requests without port
        PORT_NUMBER: "8080"
        # Server name of this container
        SERVER_NAME: "crusoe-act-overseer"

  crusoe_act_component:
    build:
      context: ./crusoe_act/act-component
      args:
        # URL where the act component is active, leave as it is when component is running inside the container
        PROXY_URL: "http://127.0.0.1"
        # Port on which component will start, after that we will use apache2 to proxy without port number to endpoint URL
        PORT_NUMBER: "8086"
        # Enpoint URL on which the component will accept http requests
        URL_PATH: "firewall"
        # Name of the component folder which will be copied to the container and run
        DST_WRAPPER: "simulated-pao-firewall"
        # Name of the component project name inside DST_WRAPPER folder
        WRAPPER: "firewall_wrapper"
        # Server name of component
        SERVER_NAME: "simulated-pao-firewall.local"
        # IP/Hostname of host where neo4j db is running
        EXTERNAL_IP: "${OBSERVE_IP}"
        # Password to the neo4j database
        VAULT_NEO4J_PASSWORD: "password"
        # This PAOs IP address to be written to neo4j db - the same as the docker container
        PAO_IP: "${ACT_COMPONENT_IP}"
        # PAO Name to be written into neo4j db
        PAO_NAME: "firewall"
        # Port on which the PAO will accept http requests
        PORTNUMBER: "8086"
        # Max capacity of PAO
        MAXCAPACITY: "10"
        # Current used capacity of PAO
        USEDCAPACITY: "0"
        # Current not used capacity of PAO
        FREECAPACITY: "10"



  crusoe_observe:
    build:
      context: ./crusoe_observe
      args:
        # Port on which neo4j-rest REST API will start, we will use apache2 proxy to access the REST API without port
        NEO4J_REST_PORT: "8080"
        # neo4j-rest server name for apache2
        SERVER_NAME: "neo4j-rest"
        # Password to the neo4j db that will be set on the startup of container
        NEO4J_PASSWORD: "password"

  crusoe_graphql:
    build:
      context: ./graphql-api
      args:
        # Port on which graphql service will be available
        GRAPHQL_SERVER_PORT: "4001"
        # Neo4j database URL
        NEO4J_URL: "bolt://${OBSERVE_IP}:7687"
        NEO4J_USER: "neo4j"
        NEO4J_PASS: "password"

  crusoe_orient:
    build:
      context: ./crusoe_orient
      args:
        #ACT_API_URL: "http://155.54.180.23:81/act
        NEO4J_REST_URL: "http://${HOST_IP}:83/"
        # # URL Where Flower backend is available
        FLOWER_URL: "http://${HOST_IP}:5555/"
        # # URL Where act-overseer is available
        ACT_API_URL: "http://${HOST_IP}:8080/act"
        # # URL Where graphql is available
        GRAPHQL_URL: "http://${HOST_IP}:15541/graphql"
        # # URL Where the simulated firewall is available
        FIREWALL_PAO_URL: "http://${HOST_IP}:8086/firewall"
        # # RECOMMENDER
        RECOMMENDER_API: "http://${HOST_IP}:16005/"
