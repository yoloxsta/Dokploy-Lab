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

###
```
Make it permanent

Add it to your bash profile:

echo 'source <(kubectl completion bash)' >> ~/.bashrc

Then reload:

source ~/.bashrc
```
