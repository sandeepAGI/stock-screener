import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { WeightsProvider } from './context/WeightsContext';
import { OperationProvider } from './context/OperationContext';
import { Sidebar } from './components/common/Sidebar';
import { Dashboard } from './components/Dashboard/Dashboard';
import { StockAnalysis } from './components/StockAnalysis/StockAnalysis';
import { DataManagement } from './components/DataManagement/DataManagement';

function App() {
  return (
    <WeightsProvider>
      <OperationProvider>
        <BrowserRouter>
          <div className="flex h-screen bg-gray-50">
            <Sidebar />
            <main className="flex-1 overflow-auto">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/rankings" element={<Navigate to="/" replace />} />
                <Route path="/analysis" element={<StockAnalysis />} />
                <Route path="/data" element={<DataManagement />} />
              </Routes>
            </main>
          </div>
        </BrowserRouter>
      </OperationProvider>
    </WeightsProvider>
  );
}

export default App;
