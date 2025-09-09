### STAGE 1: Build ###
FROM node:12 AS build
WORKDIR /usr/src/app
COPY package.json package-lock.json ./
RUN npm install --legacy-peer-deps
COPY . .

ARG NEO4J_REST_URL="http://localhost/"
ARG FLOWER_URL="http://localhost:5555/"
ARG ACT_API="http://localhost:8080/act/"
ARG GRAPHQL_URL="http://localhost:4001/graphql"
ARG FIREWALL_PAO_URL="http://localhost/firewall"
ARG RECOMMENDER_API: "http://localhost:16005/recommender"

RUN sed -i "s|baseUrl: .*|baseUrl: '/rest/',|"           ./src/environments/environment.prod.ts \
  && sed -i "s|flowerUrl: .*|flowerUrl: '/flower/',|"     ./src/environments/environment.prod.ts \
  && sed -i "s|tmpActApi: .*|tmpActApi: '/act/',|"        ./src/environments/environment.prod.ts \
  && sed -i "s|graphqlApi: .*|graphqlApi: '/graphql',|"   ./src/environments/environment.prod.ts \
  && sed -i "s|firewallApi: .*|firewallApi: '/firewall',|" ./src/environments/environment.prod.ts \
  && sed -i "s|recommenderApi: .*|recommenderApi: '/recommender',|" ./src/environments/environment.prod.ts
RUN echo $GRAPHQL_URL
RUN echo $RECOMMENDER_API

RUN npm run build

### STAGE 2: Run ###
FROM nginx
COPY ./docker-config/dashboard.conf /etc/nginx/nginx.conf
COPY --from=build /usr/src/app/dist /usr/share/nginx/html
RUN echo $RECOMMENDER_API