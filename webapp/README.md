# Bioprocess Twin - Frontend Web Application

React-based electronic lab notebook for manual batch data collection during Pichia pastoris fermentation campaigns.

## Tech Stack

- **React 18** with TypeScript
- **Vite** - Fast build tool and dev server
- **React Router v6** - Client-side routing
- **Axios** - HTTP client with interceptors
- **React Hook Form** - Form validation
- **Zod** - Schema validation
- **JWT** - Authentication
- **date-fns** - Date utilities

## Project Structure

```
webapp/
├── src/
│   ├── api/              # API client and service layer
│   │   └── client.ts     # Axios instance, interceptors, API methods
│   ├── components/       # Reusable components
│   │   └── ProtectedRoute.tsx
│   ├── contexts/         # React contexts
│   │   └── AuthContext.tsx
│   ├── pages/            # Page components
│   │   ├── Login.tsx
│   │   ├── BatchList.tsx
│   │   ├── CreateBatch.tsx
│   │   └── BatchDashboard.tsx
│   ├── types/            # TypeScript type definitions
│   │   └── index.ts
│   ├── App.tsx           # Main app component with routing
│   └── main.tsx          # Entry point
├── .env.example          # Environment variables template
└── package.json
```

## Current Implementation Status

### ✅ Completed
- Project setup with Vite + React + TypeScript
- API client with axios interceptors for JWT
- Authentication flow (login, logout, protected routes)
- Type-safe API calls matching backend schema
- Batch listing page with status indicators
- Batch creation form with validation
- Batch dashboard with data display
- Responsive design optimized for tablet use

### 🚧 Pending (Modal Forms)
The following modal forms are referenced in BatchDashboard.tsx but not yet implemented:
1. **Calibration form** - Add pH, DO, Temp calibrations
2. **Inoculation form** - Log T=0 inoculation with GO/NO-GO decision
3. **Sample form** - Add timepoint samples (OD600, DCW, contamination)
4. **Failure form** - Report deviations with severity levels
5. **Closure form** - Close batch with engineer approval

### Next Steps
1. Create modal form components for calibration, inoculation, sample, failure, closure
2. Implement real-time data refresh after form submissions
3. Add Docker configuration for production deployment
4. Add offline-first capabilities with retry queue
5. Implement QR code scanning for vessel IDs

## Development

### Prerequisites
- Node.js 18+ and npm
- Backend API running on http://localhost:8000

### Install Dependencies
```bash
npm install
```

### Environment Configuration
```bash
cp .env.example .env
```

Edit `.env` to point to your API:
```
VITE_API_URL=http://localhost:8000/api/v1
```

### Run Development Server
```bash
npm run dev
```

Access at: http://localhost:5173

### Build for Production
```bash
npm run build
```

Output in `dist/` directory.

### Preview Production Build
```bash
npm run preview
```

## API Integration

The frontend communicates with the FastAPI backend via REST endpoints:

- `POST /auth/login` - User authentication
- `GET /batches` - List all batches
- `POST /batches` - Create new batch
- `GET /batches/{id}` - Get batch details
- `POST /batches/{id}/calibrations` - Add calibration
- `POST /batches/{id}/inoculation` - Log inoculation
- `POST /batches/{id}/samples` - Add sample
- `POST /batches/{id}/failures` - Report failure
- `POST /batches/{id}/close` - Close batch

All endpoints (except login) require JWT authentication via `Authorization: Bearer <token>` header.

## Authentication

The app uses JWT tokens stored in localStorage:
- Login stores `access_token` and `user` object
- Axios interceptor automatically adds token to requests
- 401 responses trigger automatic logout and redirect
- Protected routes redirect unauthenticated users to login

## Default Users (Development)

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | admin |
| tech01 | admin123 | technician |
| eng01 | admin123 | engineer |

## Tablet Optimization

The UI is optimized for tablet use on the Jetson AGX Orin:
- Touch-friendly button sizes (min 44x44px)
- Responsive grid layouts
- Large, readable fonts (16-18px base)
- High-contrast color scheme
- Finger-friendly form inputs

## Workflow

1. **Login** - Authenticate with username/password
2. **Batch List** - View all batches, create new batch
3. **Batch Dashboard** - View/add calibrations, inoculation, samples, failures
4. **Quality Gates**:
   - Cannot inoculate until all calibrations pass (pH, DO, Temp)
   - Cannot close until ≥8 samples collected
   - Batch closure requires engineer role
5. **Status Progression**: pending → running (after inoculation) → complete

## TypeScript Types

All API request/response types are defined in `src/types/index.ts` and match the Pydantic schemas from the backend. This ensures type safety across the full stack.

## Error Handling

- Axios interceptor catches 401 errors and redirects to login
- Form validation uses react-hook-form with inline error display
- API errors shown as banners with retry options
- Network errors handled gracefully with user feedback

## Future Enhancements

- Offline mode with IndexedDB caching
- Real-time updates via WebSocket
- QR code scanner for vessel/cryo-vial IDs
- Export batch data to CSV/PDF
- Batch comparison and analytics dashboard
- Push notifications for critical failures
