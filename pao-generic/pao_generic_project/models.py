# models.py

# Este archivo define algunos modelos de datos principales que usa  CRUSOE, estos estarán representados en grafos
# donde cada entidad de la red (hosts, servicios, vulnerabilidades, etc.) se representa 
# como un nodo o relación. A continuación se han creado como ejemplo posibles modelos Django para dichas entidades.

from django.db import models

# Node (Nodo de red): Representa un host o dispositivo en la red de la organización.
# Los host de la red se almacena como un nodo, incluyendo atributos como su nombre (identificador), tipo (ej. servidor o estación de trabajo) 
# y sistema operativo. Según la documentación, por cada host se recopila información de sistema operativo 
# (nombre y versión) y otros detalles relevantes por lo que este modelo podría tener campos. Además, un Node puede asociarse con varias direcciones IP 
# y servicios de red que corren en él.
class Node(models.Model):
    # Ejemplo de campos 
    # hostname = models.CharField(max_length=100)        # Nombre o identificador del host
    # os_name = models.CharField(max_length=50)          # Nombre del sistema operativo
    # node_type = models.CharField(max_length=50)        # Tipo de nodo (ej. "Servidor", "Workstation")
    # org_unit = models.ForeignKey('OrganizationalUnit', on_delete=models.SET_NULL, null=True, blank=True) Unidad organizacional al que pertenece el nodo (puede ser null)
    pass

# IPAddress (Dirección IP): Representa una dirección IP asignada a uno de los nodos de la red.
# Un mismo Node puede tener múltiples direcciones IP en formato texto e IPv4/IPv6, 
class IPAddress(models.Model):
    # Ejemplo de campos 
    # address = models.GenericIPAddressField()  # Dirección IP
    # node = models.ForeignKey(Node, on_delete=models.CASCADE)  # Nodo al que pertenece esta IP
    pass

# Service (Servicio de Red): Representa un servicio o aplicación que se ejecuta en un host.
# La documentación indica que por cada host se recopilan los puertos abiertos y los servicios de red, incluyendo nombre 
# y versión del software subyacente.
class Service(models.Model):
    # Ejemplo de campos 
    # name = models.CharField(max_length=100)       # Nombre del servicio (ej. "Apache HTTP Server")
    # port = models.IntegerField()                  # Puerto en el que escucha
    # protocol = models.CharField(max_length=10)    # Protocolo 
    # version = models.CharField(max_length=50)     # Versión del software 
    # node = models.ForeignKey(Node, on_delete=models.CASCADE)   # Host en el que corre este servicio
    pass

# Vulnerability (Vulnerabilidad): Representa una vulnerabilidad conocida que puede afectar a activos de la red.
# El modelo almacenaría campos como el identificador CVE, descripción, puntuación de severidad (CVSS) y referencias.
class Vulnerability(models.Model):
    # Ejemplo de campos 
    # cve_id = models.CharField(max_length=20, unique=True)   # Identificador CVE
    # description = models.TextField()                        # Descripción de la vulnerabilidad
    # cvss_score = models.FloatField(null=True, blank=True)   # Puntuación CVSS (si disponible)
    # affected_products = models.ManyToManyField(Service, blank=True)  
    #                # Relación muchos-a-muchos
    pass

# SecurityEvent (Evento de Seguridad): Representa un evento o incidente de seguridad detectado en la red 
# (por ejemplo, alertas de un IDS, eventos de logs anómalos, etc.). 
# Mantener estos eventos en un modelo permite construir un historial de incidentes de seguridad asociados a hosts o segmentos 
#. Este modelo incluiría campos como fecha/hora del evento, tipo , severidad, descripción.
class SecurityEvent(models.Model):
    # Ejemplo de campos 
    # timestamp = models.DateTimeField()              # Fecha  del evento
    # event_type = models.CharField(max_length=50)    # Tipo de evento
    # severity = models.CharField(max_length=20)      # Severidad 
    # description = models.TextField()                # Descripción detallada del evento
    # source_ip = models.ForeignKey(IPAddress, on_delete=models.SET_NULL, null=True, related_name='events_source')
    #                # IP origen del evento 
    # target_node = models.ForeignKey(Node, on_delete=models.SET_NULL, null=True, related_name='events_target')
    #                # Nodo objetivo afectado por el evento 
    pass

# OrganizationalUnit (UnidadOrganizacional): Representa una unidad organizativa dentro de la organización. Serviría para categorizar los hosts  según su ubicación física o responsabilidad administrativa:contentReference[oaicite:10]{index=10}. 
# Cada Node podría tener una ForeignKey a este modelo indicando a qué unidad o segmento pertenece, facilitando consultas por área responsable.
class OrganizationalUnit(models.Model):
    # Ejemplo de campos 
    # name = models.CharField(max_length=100)                 # Nombre del departamento 
    # description = models.TextField(blank=True)              # Descripción
    pass

# Mission (Misión): Representa una misión empresarial o proceso de negocio que depende de la infraestructura de TI.
# Este modelo contendría campos como nombre de la misión, descripción y criticidad, y se relacionaría con los nodos o servicios de la red 
# que la habilitan. Podríamos usar una relación muchos-a-muchos entre Mission y Node (o Service) para reflejar qué hosts/servicios apoyan cada misión.
class Mission(models.Model):
    # Ejemplo de campos 
    # name = models.CharField(max_length=100)       # Nombre de la misión (ej. "Servicio de Correo Corporativo")
    # description = models.TextField(blank=True)    # Descripción del proceso o servicio empresarial
    # criticality = models.CharField(max_length=20, blank=True)  # Criticidad o nivel de importancia 
    # assets = models.ManyToManyField(Node, blank=True) # Activos que soportan la misión. 
    pass
