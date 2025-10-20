from django.contrib import admin
from .models import Node, IPAddress, Service, Vulnerability, SecurityEvent, OrganizationalUnit, Mission

# Registramos cada modelo relevante en la interfaz de administración de Django:

# Node: para poder ver y editar los hosts de la red y sus detalles 
admin.site.register(Node)
# IPAddress: permite visualizar y editar direcciones IP asociadas a los hosts 
admin.site.register(IPAddress)
# Service: para administrar los servicios de red detectados en los nodos 
admin.site.register(Service)
# Vulnerability: para consultar y actualizar la base de datos de vulnerabilidades (CVE) conocida por el sistema.
admin.site.register(Vulnerability)
# SecurityEvent: para revisar el historial de eventos/alertas de seguridad registrados, filtrarlos por fecha o host afectado, etc.
admin.site.register(SecurityEvent)
# OrganizationalUnit: para gestionar la estructura organizativa o segmentación de la red.
admin.site.register(OrganizationalUnit)
# Mission: para visualizar y editar las misiones o procesos de negocio y sus vinculaciones con los activos de TI, lo que ayuda a evaluar el impacto de incidentes en la misión empresarial.
admin.site.register(Mission)