# Docker Setup Instructions

## Prerequisites
1. Copy your Cloudflare tunnel credentials file to:
   ```
   ./cloudflared/1128574d-8095-4d02-8402-3f95dd33e546.json
   ```

## Build and Run

### Start all services:
```bash
docker-compose up -d
```

### View logs:
```bash
# All services
docker-compose logs -f

# Django only
docker-compose logs -f web

# Cloudflared only
docker-compose logs -f cloudflared
```

### Stop services:
```bash
docker-compose down
```

### Rebuild after code changes:
```bash
docker-compose up -d --build
```

## Access
- Local: http://localhost:8000
- Public: https://app.sangam1313.com.np

## Troubleshooting

### Check container status:
```bash
docker-compose ps
```

### Restart specific service:
```bash
docker-compose restart web
docker-compose restart cloudflared
```

### View Django migrations:
```bash
docker-compose exec web python manage.py showmigrations
```

### Access Django shell:
```bash
docker-compose exec web python manage.py shell
```
