# K8s Manifests

- 📁 File Organization

```
├── deployment.yaml                      # creates deployment for enterprise-rag
├── service.yaml                         # creates loadbalancer service for target port
├── serviceacc-namespace.yaml            # creates service account and namespace
├── /eso-manifests/                   
    ├── eso-ClusterSecretStores.yaml     # ESO ClusterSecretStore for aws-parameterstore
    ├── eso-ExternalSecret.yaml          # ESO ExternalSecret for aws parameterstore
```
