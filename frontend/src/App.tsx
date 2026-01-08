import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom'
import { Beaker, Target, BookOpen } from 'lucide-react'
import PredictPage from './pages/PredictPage'
import OptimizePage from './pages/OptimizePage'
import ReferencePage from './pages/ReferencePage'

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-blue-600 rounded-lg flex items-center justify-center">
                  <Beaker className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-xl font-bold text-gray-900">AlloyPredictor</h1>
                  <p className="text-sm text-gray-500">AI-прогнозирование свойств сплавов</p>
                </div>
              </div>

              {/* Navigation */}
              <nav className="flex gap-1">
                <NavLink
                  to="/"
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`
                  }
                >
                  <Beaker className="w-4 h-4" />
                  Прогноз
                </NavLink>
                <NavLink
                  to="/optimize"
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`
                  }
                >
                  <Target className="w-4 h-4" />
                  Оптимизация
                </NavLink>
                <NavLink
                  to="/reference"
                  className={({ isActive }) =>
                    `flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:bg-gray-100'
                    }`
                  }
                >
                  <BookOpen className="w-4 h-4" />
                  Справочник
                </NavLink>
              </nav>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="max-w-7xl mx-auto px-4 py-8">
          <Routes>
            <Route path="/" element={<PredictPage />} />
            <Route path="/optimize" element={<OptimizePage />} />
            <Route path="/reference" element={<ReferencePage />} />
          </Routes>
        </main>

        {/* Footer */}
        <footer className="border-t bg-white py-4 mt-8">
          <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500">
            AlloyPredictor v1.0 - Система прогнозирования свойств сплавов на основе машинного обучения
          </div>
        </footer>
      </div>
    </BrowserRouter>
  )
}

export default App
