import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './contexts/AuthContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { BatchList } from './pages/BatchList';
import { CreateBatch } from './pages/CreateBatch';
import { BatchDashboard } from './pages/BatchDashboard';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes */}
          <Route
            path="/batches"
            element={
              <ProtectedRoute>
                <BatchList />
              </ProtectedRoute>
            }
          />
          <Route
            path="/batches/new"
            element={
              <ProtectedRoute>
                <CreateBatch />
              </ProtectedRoute>
            }
          />
          <Route
            path="/batches/:batchId"
            element={
              <ProtectedRoute>
                <BatchDashboard />
              </ProtectedRoute>
            }
          />

          {/* Default redirect */}
          <Route path="/" element={<Navigate to="/batches" replace />} />
          <Route path="*" element={<Navigate to="/batches" replace />} />
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;
