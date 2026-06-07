import { Navigate, Route, Routes } from 'react-router-dom';
import { AppLayout } from '../components/layout/AppLayout';
import { routes } from '../config/routes';

export function App() {
  return (
    <Routes>
      <Route element={<AppLayout />}>
        {routes.map((route) => (
          <Route key={route.path} path={route.path} element={<route.element />} />
        ))}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
