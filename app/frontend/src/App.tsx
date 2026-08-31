import { Routes, Route } from 'react-router-dom';
import { Header } from './components/Header';
import { RoleSelection } from './pages/RoleSelection';
import { ExecutivePage } from './pages/ExecutivePage';
import { CustomerPage } from './pages/CustomerPage';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-db-bg text-db-text">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<RoleSelection />} />
          <Route path="/exec" element={<ExecutivePage />} />
          <Route path="/customer" element={<CustomerPage />} />
        </Routes>
      </main>
    </div>
  );
}
