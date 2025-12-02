import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/common/Sidebar';
import { Dashboard } from './components/Dashboard/Dashboard';
import { Rankings } from './components/Rankings/Rankings';
import { StockAnalysis } from './components/StockAnalysis/StockAnalysis';
import { DataManagement } from './components/DataManagement/DataManagement';

function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50">
        <Sidebar />
        <main className="flex-1 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/rankings" element={<Rankings />} />
            <Route path="/analysis" element={<StockAnalysis />} />
            <Route path="/data" element={<DataManagement />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
