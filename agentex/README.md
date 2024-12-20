# Agentex

## Getting Started

### Installation

```commandline
brew install minikube
brew install derailed/k9s/k9s
brew install helm
brew install helmfile
helm plugin install https://github.com/databus23/helm-diff

conda create -n agentex python=3.12
conda activate agentex

pip install poetry

make install
```

## Development

### Start minikube
```commandline
minikube start --cpus 4 --memory 16384
```

### Create secret to push and pull from private dockerhub registry
```commandline
kubectl create secret docker-registry hosted-actions-regcred \
  --docker-server=https://index.docker.io/v1/ \
  --docker-username=<username> \
  --docker-password=<personal_access_token> \
  --docker-email=<email>
```

### Create secret to store your openai api key
```commandline
kubectl create secret generic openai-api-key \
  --from-literal=api-key='your_openai_api_key' \
  --namespace default
```

### Create secret to store the openai api key and any other secrets for your agents
```commandline 
kubectl create secret generic openai-api-key \
  --from-literal=api-key='your_openai_api_key' \
  --namespace agentex-agents
```

### Install Helm charts and run the server
```commandline
make dev
make port-forward # If the port forwarding is attempted before the pod is ready
```

### Temporal

One time setup (See: https://github.com/temporalio/helm-charts?tab=readme-ov-file#running-temporal-cli-from-the-admin-tools-container)
```commandline
kubectl exec -it services/temporaltest-admintools /bin/bash
tctl --ns default namespace desc  # if not found
tctl --ns default namespace re
```


### Redis

```commandline
(agentx) felixsu@Felixs-MacBook-Pro-2 charts % helm install redis ./redis 
NAME: redis
LAST DEPLOYED: Thu Oct  3 22:44:31 2024
NAMESPACE: default
STATUS: deployed
REVISION: 1
TEST SUITE: None
NOTES:
CHART NAME: redis
CHART VERSION: 20.1.7
APP VERSION: 7.4.1

** Please be patient while the chart is being deployed **

Redis&reg; can be accessed on the following DNS names from within your cluster:

    redis-master.default.svc.cluster.local for read/write operations (port 6379)
    redis-replicas.default.svc.cluster.local for read-only operations (port 6379)



To get your password run:

    export REDIS_PASSWORD=$(kubectl get secret --namespace default redis -o jsonpath="{.data.redis-password}" | base64 -d)

To connect to your Redis&reg; server:

1. Run a Redis&reg; pod that you can use as a client:

   kubectl run --namespace default redis-client --restart='Never'  --env REDIS_PASSWORD=$REDIS_PASSWORD  --image docker.io/bitnami/redis:7.4.1-debian-12-r0 --command -- sleep infinity

   Use the following command to attach to the pod:

   kubectl exec --tty -i redis-client \
   --namespace default -- bash

2. Connect using the Redis&reg; CLI:
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h redis-master
   REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h redis-replicas

To connect to your database from outside the cluster execute the following commands:

    kubectl port-forward --namespace default svc/redis-master 6379:6379 &
    REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli -h 127.0.0.1 -p 6379

WARNING: There are "resources" sections in the chart not set. Using "resourcesPreset" is not recommended for production. For production installations, please set the following values according to your workload needs:
  - replica.resources
  - master.resources
+info https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/

```

# TODO
- [ ] Secure secrets with helm secrets
- [ ] Templatize hardcoded values (like registry)
- [ ] Separate deployments for each temporal worker pool