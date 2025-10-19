# Quick Start Guide - Manual Data Collection System

## Prerequisites

- Docker Desktop installed and running
- Git (to clone/manage the repository)

## Step 1: Start the Services

```bash
# From the project root directory
docker-compose up -d
```

This will start:
- **PostgreSQL** database on port 5432
- **FastAPI** backend on port 8000

## Step 2: Verify Services are Running

```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f api
```

## Step 3: Access the API Documentation

Open your browser to:
- **Swagger UI:** http://localhost:8000/api/v1/docs
- **ReDoc:** http://localhost:8000/api/v1/redoc

## Step 4: Test Authentication

### Login with default credentials

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }'
```

You'll receive a JWT token:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Use the token for authenticated requests

```bash
# Set token as variable
TOKEN="your_token_here"

# Create a batch
curl -X POST http://localhost:8000/api/v1/batches \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "batch_number": 1,
    "phase": "A",
    "vessel_id": "V-01",
    "operator_id": "USER:T001",
    "notes": "Test batch"
  }'
```

## Step 5: Example Workflow

### 1. Create a batch
```bash
POST /api/v1/batches
{
  "batch_number": 1,
  "phase": "A",
  "vessel_id": "V-01",
  "operator_id": "USER:T001"
}
```

### 2. Log calibrations (pH, DO, Temp)
```bash
POST /api/v1/batches/{batch_id}/calibrations
{
  "probe_type": "pH",
  "buffer_low_value": 4.01,
  "buffer_high_value": 7.00,
  "reading_low": 4.02,
  "reading_high": 6.98,
  "pass": true,
  "calibrated_by": "USER:T001"
}
```

### 3. Log inoculation (sets T=0)
```bash
POST /api/v1/batches/{batch_id}/inoculation
{
  "cryo_vial_id": "CRYO-001",
  "inoculum_od600": 4.5,
  "microscopy_observations": "Healthy cells, no contamination",
  "go_decision": true,
  "inoculated_by": "USER:T001"
}
```

### 4. Add samples
```bash
POST /api/v1/batches/{batch_id}/samples
{
  "od600_raw": 2.5,
  "od600_dilution_factor": 1.0,
  "contamination_detected": false,
  "sampled_by": "USER:T001"
}
```

### 5. Close batch (requires engineer role)
```bash
POST /api/v1/batches/{batch_id}/close
{
  "final_od600": 45.2,
  "total_runtime_hours": 16.5,
  "glycerol_depletion_time_hours": 14.2,
  "outcome": "Complete",
  "closed_by": "USER:T001",
  "approved_by": "USER:E001"
}
```

## Default Users

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| tech01 | admin123 | technician |
| eng01 | admin123 | engineer |

**⚠️ IMPORTANT:** Change these passwords in production!

## Stopping the Services

```bash
# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Stop and remove containers + volumes (deletes all data)
docker-compose down -v
```

## Troubleshooting

### Database connection errors
```bash
# Check postgres is healthy
docker-compose ps postgres

# View postgres logs
docker-compose logs postgres
```

### API errors
```bash
# View API logs
docker-compose logs api

# Restart API
docker-compose restart api
```

### Reset database
```bash
# Stop services
docker-compose down -v

# Start fresh
docker-compose up -d
```

## Next Steps

1. **Change default passwords** in production
2. **Configure CORS** for your tablet IPs in `.env`
3. **Set up backups** using the scripts in `scripts/`
4. **Deploy React frontend** (see `webapp/README.md`)

## Development Mode

For development with hot reload:

```bash
# API will reload on code changes
docker-compose up

# Or just the API
docker-compose up api
```

## API Documentation

Full API documentation is available at:
- Interactive: http://localhost:8000/api/v1/docs
- Reference: docs/manual-data-development.md
