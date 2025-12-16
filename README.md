# CRUSOE - Cyber Situational Awareness Platform

CRUSOE is an open-source Cyber Situational Awareness (CySA) platform that implements the OODA loop (Observe, Orient, Decide, Act) for incident handling and decision support. This fork extends the original [CRUSOE](https://github.com/CSIRT-MU/CRUSOE) with bug fixes, deployment improvements, and a new **Recommender System** with actionable CVE recommendations.


## Quickstart

### Prerequisites

- Docker & Docker Compose
- 8GB+ RAM recommended
- Default Ports: 80, 5555, 7474, 8080, 8086, 16005 (they can be changed to adapt to the enviromental requisits)

### 1. Clone and Configure

```bash
git clone https://github.com/AnthonyFA/CDLCRUSOE.git
cd CDLCRUSOE
```
Edit `.env` file with your network configuration:
```env
HOST_IP=your.server.ip
NEO4J_PASSWORD=password
```

### 2.Build
```bash
# Build all containers (takes ~10 minutes)
docker compose build --no-cache

# Start Observe module first (initializes Neo4j)
docker compose up crusoe_observe -d

# Wait for Neo4j to be ready, then load sample data
./loaddataset.sh

# Start all services
docker compose up -d

# Restart Orient to refresh dashboard data
docker compose restart crusoe_orient
```

Once the scenario is launched it will be necessary to check if the Neo4j Database is active, so we must access the observer container and see if it is running:
``` shell
docker exec -it "ID"  /bin/bash
neo4j status
```

Once it finishes running, access the link where CRUSOE is displayed, and enter the values **neo4j:password** as user:password. 


## Modifications
The modifications made to put in operation the original CRUSOE has been the adaptation of neo4j in the file **crusoe_observer/Dockerfile**, where the version `neo4j=1:4.4.41` and `stable 4.4` have been added so that this will have a more updated version. In addition, a number of plugins have been added to make them work:
```
COPY ansible/roles/neo4j/files/apoc-4.4.0.35-all.jar /var/lib/neo4j/plugins/
COPY ansible/roles/neo4j/files/neo4j-graph-data-science-2.3.0.jar /var/lib/neo4j/plugins/
```
### URL and IPs
Another modified element in this project has been the IPs shown throughout the **docker-compose.yml**, where we have set the IP of the local machine we have worked with throughout our research project. So if you want to deploy it on your own, we recommend that you use a local or respective network to set up the scenario.

For example, on the following code we can see we have modified previous IP directions with our own, taking into account that all our modified directions has the same IP value. Futhermore, the **bride_crusoe** IP has`nt been modifed because they have still not been use:
``` python
    build:
      context: ./crusoe_orient
      args:
        NEO4J_REST_URL: "http://172.22.104.217/rest/" #"http://192.168.5.136/rest/"
        # # URL Where Flower backend is available
        FLOWER_URL: "http://172.22.104.217:5555/" #"http://192.168.5.136:5555/"
        # # URL Where act-overseer is available
        ACT_API_URL: "http://172.22.104.217/act" #"http://192.168.5.136/act"
        # # URL Where graphql is available
        GRAPHQL_URL: "http://172.22.104.217:4001/graphql" #"http://192.168.5.136:4001/graphql"
        # # URL Where the simulated firewall is available
        FIREWALL_PAO_URL: "http://172.22.104.217:8086/firewall" #"http://192.168.5.136:8086/firewall"
        # # RECOMMENDER
        RECOMMENDER_API: "http://172.22.104.217:16005/recommender" #"http://192.168.5.136:16005/recommender"
```
## 🔗 References

- [Original CRUSOE Repository](https://github.com/CSIRT-MU/CRUSOE)
- [CRUSOE Paper (Husak et al.)](https://doi.org/10.1016/j.cose.2022.102609)
- [Recommender System Paper](https://doi.org/10.1007/978-3-030-91625-5_6)
- [NVD API 2.0 Documentation](https://nvd.nist.gov/developers/vulnerabilities)

## 📄 License

This project is licensed under the BSD-3-Clause License - see the [LICENSE](LICENSE) file for details.

## 👤 Author

**Antonio López Martínez ** - Master's Thesis Project  
University of Murcia

---

*This fork was developed as part of a Master's Thesis on Cyber Situational Awareness platforms.*

