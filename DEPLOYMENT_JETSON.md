# Deployment Guide - Jetson AGX Orin

This guide covers deploying the Manual Data Collection System on the Jetson AGX Orin.

## Pre-Deployment Checklist

- [ ] Jetson AGX Orin running Ubuntu 22.04
- [ ] Docker and Docker Compose installed
- [ ] Git installed
- [ ] Network connectivity confirmed
- [ ] Firewall rules configured (ports 5432, 8000, 3000)

## Step 1: Clone Repository on Jetson

```bash
# SSH into Jetson
ssh admin@jetson-edge.local

# Clone repository
git clone https://github.com/ScionResearch/bioprcoess-twin.git
cd bioprcoess-twin

# Verify latest commit
git log --oneline -1
# Should show: feat: implement complete manual data collection backend (v0.2.0)
```

## Step 2: Configure Environment

```bash
# Copy environment template
cp api/.env.example api/.env

# Edit with secure values
nano api/.env
```

**Important environment variables to set:**

```bash
# Database password (CHANGE THIS!)
POSTGRES_PASSWORD=<generate_secure_password>

# JWT secret key (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=<your_jwt_secret>

# CORS origins (add your tablet IPs)
ALLOWED_ORIGINS=http://tablet-01.local,http://tablet-02.local,http://workstation.local
```

**Generate secure passwords:**
```bash
# For Postgres password
openssl rand -base64 32

# For JWT secret
openssl rand -hex 32
```

## Step 3: Deploy Services

```bash
# Build and start services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f api
```

Expected output:
```
NAME                IMAGE               STATUS
pichia-postgres     postgres:15-alpine  Up (healthy)
pichia-api          bioprocess-twin-api Up
```

## Step 4: Verify Database Initialization

```bash
# Connect to PostgreSQL
docker exec -it pichia-postgres psql -U pichia_api -d pichia_manual_data

# Check tables
\dt

# Verify seed users
SELECT username, role FROM users;

# Exit psql
\q
```

Expected tables:
- audit_log
- batch_closures
- batches
- calibrations
- failures
- inoculations
- media_preparations
- process_changes
- samples
- users

## Step 5: Test API

```bash
# Health check
curl http://localhost:8000/health

# Login as admin
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# Save the token
export TOKEN="<paste_token_here>"

# Create a test batch
curl -X POST http://localhost:8000/api/v1/batches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_number": 1,
    "phase": "A",
    "vessel_id": "V-01",
    "operator_id": "USER:T001",
    "notes": "Test batch from Jetson"
  }'
```

## Step 6: Change Default Passwords

**CRITICAL SECURITY STEP!**

```bash
# Connect to database
docker exec -it pichia-postgres psql -U pichia_api -d pichia_manual_data

# Update admin password (use bcrypt hash)
# Generate hash: python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_new_password'))"

UPDATE users
SET password_hash = '$2b$12$<your_bcrypt_hash>'
WHERE username = 'admin';

# Verify
SELECT username, active FROM users WHERE username = 'admin';

# Exit
\q
```

## Step 7: Configure Networking

### Firewall Rules

```bash
# Allow API access
sudo ufw allow 8000/tcp

# Allow Postgres (internal only - optional)
sudo ufw allow from <tablet_ip> to any port 5432

# Check status
sudo ufw status
```

### Static IP Configuration (if needed)

```bash
# Edit netplan
sudo nano /etc/netplan/01-network-manager-all.yaml

# Add static IP configuration
# See PROJECT_STRUCTURE.md for example
```

## Step 8: Set Up Backups

```bash
# Create backup directory
sudo mkdir -p /mnt/backup/postgres

# Copy backup script
sudo cp scripts/backup_postgres.sh /usr/local/bin/
sudo chmod +x /usr/local/bin/backup_postgres.sh

# Add to crontab
crontab -e

# Add line:
# 0 2 * * * /usr/local/bin/backup_postgres.sh >> /var/log/postgres_backup.log 2>&1
```

## Step 9: Access API Documentation

From your workstation browser:

- **Swagger UI:** http://jetson-edge.local:8000/api/v1/docs
- **ReDoc:** http://jetson-edge.local:8000/api/v1/redoc

## Step 10: Monitor Services

```bash
# View logs in real-time
docker-compose logs -f

# Check service health
docker-compose ps

# Restart services if needed
docker-compose restart api

# View resource usage
docker stats
```

## Troubleshooting

### API won't start

```bash
# Check API logs
docker-compose logs api

# Common issues:
# 1. Database not ready - wait for postgres to be healthy
# 2. Missing .env file - create from .env.example
# 3. Port 8000 already in use - check with: sudo lsof -i :8000
```

### Database connection errors

```bash
# Check postgres is running
docker-compose ps postgres

# Check postgres logs
docker-compose logs postgres

# Verify connection manually
docker exec -it pichia-postgres pg_isready -U pichia_api
```

### Can't login with default credentials

```bash
# Verify users exist
docker exec -it pichia-postgres psql -U pichia_api -d pichia_manual_data -c "SELECT * FROM users;"

# If no users, database didn't initialize
# Recreate: docker-compose down -v && docker-compose up -d
```

## Performance Tuning (Jetson Specific)

### Adjust Docker resource limits

Edit `docker-compose.yml`:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: '4'
        memory: 4G
      reservations:
        cpus: '2'
        memory: 2G
```

### PostgreSQL tuning for Jetson

```bash
# Connect to postgres
docker exec -it pichia-postgres psql -U pichia_api -d pichia_manual_data

# Adjust settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET work_mem = '16MB';

# Restart postgres
docker-compose restart postgres
```

## Next Steps

1. **Deploy React Frontend** - See `webapp/README.md` (to be created)
2. **Configure Tablets** - Point browsers to `http://jetson-edge.local:8000/api/v1/docs`
3. **Set up Monitoring** - Add Grafana dashboard for API metrics
4. **Test Full Workflow** - Execute a complete batch lifecycle

## System Architecture on Jetson

```
Jetson AGX Orin
├── Docker Network: pichia-net
│   ├── postgres:5432 (PostgreSQL 15)
│   └── api:8000 (FastAPI)
├── Volumes
│   └── postgres_data (persistent storage)
└── Network Interfaces
    ├── eth0: 192.168.1.100 (internal lab network)
    └── wlan0: (optional Wi-Fi for tablets)
```

## Maintenance Commands

```bash
# Update from git
git pull origin main
docker-compose down
docker-compose up -d --build

# Backup database
docker exec pichia-postgres pg_dump -U pichia_api pichia_manual_data | gzip > backup_$(date +%Y%m%d).sql.gz

# Restore database
gunzip < backup_20251020.sql.gz | docker exec -i pichia-postgres psql -U pichia_api -d pichia_manual_data

# View disk usage
docker system df

# Clean up unused images
docker system prune -a
```

## Support

For issues during deployment:
1. Check logs: `docker-compose logs -f`
2. Verify network: `ping jetson-edge.local`
3. Check documentation: `docs/manual-data-development.md`
4. Review project structure: `PROJECT_STRUCTURE.md`

---

**Ready for production use on Jetson AGX Orin!**
