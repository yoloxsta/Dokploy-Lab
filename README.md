# Demo Service

A simple Python Flask demo service for Dokploy deployment.

## Prerequisites

- Docker installed on your server

## Dokploy Installation

### Step 1: Install Dokploy

```bash
curl -fsSL https://dokploy.com/install.sh | bash
```

### Step 2: Configure DNS (Optional)

Set up Traefik routing for your domain:

```bash
sudo tee /etc/dokploy/traefik/dynamic/dokploy.yml > /dev/null << 'EOF'
http:
  routers:
    dokploy-router-app:
      rule: Host(`dokploy.yourdomain.com`)
      service: dokploy-service-app
      entryPoints:
        - web
      middlewares:
        - redirect-to-https 
    dokploy-router-app-secure:
      rule: Host(`dokploy.yourdomain.com`)
      service: dokploy-service-app
      entryPoints:
        - websecure
      tls:
        certResolver: letsencrypt 
  services:
    dokploy-service-app:
      loadBalancer:
        servers:
          - url: http://dokploy:3000
        passHostHeader: true
EOF
```

### Step 3: Restart Traefik

```bash
sudo docker restart dokploy-traefik
```

## Deploying This Service

1. Push this repository to a Git provider (GitHub, GitLab, etc.)
2. In Dokploy, create a new application
3. Select **Git** as the provider
4. Enter your repository URL
5. Set **Build Type** to `Dockerfile`
6. Deploy!

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Welcome message |
| GET | `/health` | Health check |
| GET | `/api/items` | List all items |
| GET | `/api/items/<id>` | Get specific item |
| POST | `/api/items` | Create new item |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| PORT | 3000 | Server port |

## Local Development

```bash
pip install -r requirements.txt
python app.py
```

The service will run at `http://localhost:3000`

### Kubectl Auto Complete

```bash
# Make it permanent
echo 'source <(kubectl completion bash)' >> ~/.bashrc

# Then reload
source ~/.bashrc
```

## Troubleshooting

### Install curl in Docker Container

If `curl` is not available inside the container:

```bash
# For Debian/Ubuntu based images
apt-get update && apt-get install -y curl

# For Alpine based images
apk add --no-cache curl
```

### AGIC Issues

#### Find Available IP in App Gateway Subnet

```bash
az network vnet subnet show \
  --resource-group MC_June-RG_June-AKS_centralindia \
  --vnet-name aks-vnet-37939314 \
  --name ingress-appgateway-subnet \
  --query addressPrefix
```

Example output: `10.225.0.0/24`

#### Check Already Allocated IPs

```bash
# Check NIC IPs
az network nic list \
  --resource-group MC_June-RG_June-AKS_centralindia \
  --query "[].ipConfigurations[].privateIPAddress" \
  -o table

# Check existing App Gateway frontend IPs
az network application-gateway frontend-ip list \
  --gateway-name ingress-appgateway \
  --resource-group MC_June-RG_June-AKS_centralindia \
  -o table
```

#### Create Private Frontend with Static IP

```bash
az network application-gateway frontend-ip create \
  --gateway-name ingress-appgateway \
  --resource-group MC_June-RG_June-AKS_centralindia \
  --name privateFrontend \
  --private-ip-address 10.225.0.10 \
  --subnet ingress-appgateway-subnet \
  --vnet-name aks-vnet-37939314
```

Expected output:
```
{- Finished ..
  "id": "/subscriptions/.../frontendIPConfigurations/privateFrontend",
  "name": "privateFrontend",
  "privateIpAddress": "10.225.0.10",
  "privateIpAllocationMethod": "Static",
  "provisioningState": "Succeeded",
  "type": "Microsoft.Network/applicationGateways/frontendIPConfigurations"
}
```

#### Verify Private Frontend

```bash
az network application-gateway frontend-ip list \
  --gateway-name ingress-appgateway \
  --resource-group MC_June-RG_June-AKS_centralindia \
  -o table
```

Expected result:
```
Name                  PrivateIPAddress
--------------------  ----------------
privateFrontend       10.225.0.10
appGatewayFrontendIP
```

#### Update Ingress to Use Private IP

Before:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
spec:
  ingressClassName: azure-application-gateway
  rules:
```

After:
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
  annotations:
    appgw.ingress.kubernetes.io/use-private-ip: "true"
spec:
  ingressClassName: azure-application-gateway
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx
            port:
              number: 80
```

Apply:
```bash
kubectl apply -f ingress-test.yml
```

#### Watch AGIC Reconciliation Logs

```bash
kubectl logs -n kube-system deployment/ingress-appgw-deployment -f
```

Expected output during reconciliation:
```
I0912 10:30:00.123456       1 controller.go:123] Starting AGIC
I0912 10:30:01.234567       1 backend.go:456] Updating App Gateway
I0912 10:30:02.345678       1 listener.go:789] Created listener
```

#### Validate Setup

```bash
# Check App Gateway listener
az network application-gateway http-listener list \
  --gateway-name ingress-appgateway \
  --resource-group MC_June-RG_June-AKS_centralindia \
  -o table
```

Expected output:
```
Name                                           PrivateIpAddress
--------------------------------------------   ----------------
fl-22ee2b2b23866544c9beb9eab8459a2b            10.225.0.10
```

```bash
# Check backend health
az network application-gateway show-backend-health \
  --name ingress-appgateway \
  --resource-group MC_June-RG_June-AKS_centralindia
```

Expected output:
```
{
  "backendAddressPools": [
    {
      "backendHttpSettingsCollection": [
        {
          "servers": [
            {
              "address": "10.244.0.33",
              "health": "Healthy",
              "healthProbeLog": "Success. Received 200 status code"
            }
          ]
        }
      ]
    }
  ]
}
```

#### VNet Peering

Step 1: Get resource IDs:
```bash
az network vnet show -g June-RG -n June-VM-vnet --query id -o tsv
az network vnet show -g MC_June-RG_June-AKS_centralindia -n aks-vnet-37939314 --query id -o tsv
```

Step 2: Create peering (both directions required):

VM → AKS:
```bash
az network vnet peering create \
  --name vm-to-aks \
  --resource-group June-RG \
  --vnet-name June-VM-vnet \
  --remote-vnet "/subscriptions/ID/resourceGroups/MC_June-RG_June-AKS_centralindia/providers/Microsoft.Network/virtualNetworks/aks-vnet-37939314" \
  --allow-vnet-access
```

AKS → VM:
```bash
az network vnet peering create \
  --name aks-to-vm \
  --resource-group MC_June-RG_June-AKS_centralindia \
  --vnet-name aks-vnet-37939314 \
  --remote-vnet "/subscriptions/ID/resourceGroups/June-RG/providers/Microsoft.Network/virtualNetworks/June-VM-vnet" \
  --allow-vnet-access
```

Step 3: Verify peering:
```bash
az network vnet peering list \
  -g June-RG \
  --vnet-name June-VM-vnet \
  -o table
```

Expected output:
```
Name      PeeringState    ProvisioningState
--------  --------------- ------------------
vm-to-aks Connected       Succeeded
```

```bash
az network vnet peering list \
  -g MC_June-RG_June-AKS_centralindia \
  --vnet-name aks-vnet-37939314 \
  -o table
```

Expected output:
```
Name      PeeringState    ProvisioningState
--------  --------------- ------------------
aks-to-vm Connected       Succeeded
```

#### Start Application Gateway

```bash
az network application-gateway start \
  --name ingress-appgateway \
  --resource-group MC_June-RG_June-AKS_centralindia
```
###
```
azureuser@June-VM:~$ cat ingress-test.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
      - name: nginx
        image: nginx
        ports:
        - containerPort: 80

---
apiVersion: v1
kind: Service
metadata:
  name: nginx
spec:
  selector:
    app: nginx
  ports:
  - port: 80
    targetPort: 80
  type: ClusterIP

---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress
  annotations:
    appgw.ingress.kubernetes.io/use-private-ip: "true"
spec:
  ingressClassName: azure-application-gateway
  rules:
  - http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx
            port:
              number: 80
azureuser@June-VM:~$ cat public.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-1
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx-1
  template:
    metadata:
      labels:
        app: nginx-1
    spec:
      containers:
        - name: nginx-1
          image: nginx
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: nginx-1
spec:
  selector:
    app: nginx-1
  ports:
    - port: 80
      targetPort: 80
  type: ClusterIP
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: nginx-ingress-1
spec:
  ingressClassName: azure-application-gateway
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: nginx-1
                port:
                  number: 80
azureuser@June-VM:~$
```
