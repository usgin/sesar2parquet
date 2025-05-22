# NGINX Sidecar

## Description

Custom NGINX image deployed as a sidecar inside the sesar2-api ECS service. The sidecar is used to serve static files from the shared EFS volume and route other requests to the Django API.