import { useState } from 'react'
import { Target, Loader2, CheckCircle, AlertCircle, Beaker, DollarSign } from 'lucide-react'
import { optimizeComposition, OptimizationResponse, Composition } from '../api/client'

interface FormData {
  minYieldStrength: string
  minTensileStrength: string
  minElongation: string
  targetHardness: string
  baseElement: string
  maxCost: string
  corrosionRequirement: string
}

const COST_LABELS: Record<string, string> = {
  low: 'Низкая',
  medium: 'Средняя',
  high: 'Высокая',
}

function formatComposition(comp: Composition): string {
  return Object.entries(comp)
    .filter(([_, v]) => v && v > 0.01)
    .sort((a, b) => (b[1] || 0) - (a[1] || 0))
    .map(([k, v]) => `${k}: ${v?.toFixed(2)}%`)
    .join(', ')
}

export default function OptimizePage() {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<OptimizationResponse | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<FormData>({
    minYieldStrength: '400',
    minTensileStrength: '600',
    minElongation: '15',
    targetHardness: '',
    baseElement: 'Fe',
    maxCost: 'high',
    corrosionRequirement: '',
  })

  const handleInputChange = (field: keyof FormData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleOptimize = async () => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      // Формируем запрос на оптимизацию
      const targetProperties: Record<string, number> = {}

      if (formData.minYieldStrength) {
        targetProperties.min_yield_strength = parseFloat(formData.minYieldStrength)
      }
      if (formData.minTensileStrength) {
        targetProperties.min_tensile_strength = parseFloat(formData.minTensileStrength)
      }
      if (formData.minElongation) {
        targetProperties.min_elongation = parseFloat(formData.minElongation)
      }
      if (formData.targetHardness) {
        targetProperties.target_hardness = parseFloat(formData.targetHardness)
      }

      // Определяем ограничения по элементам на основе требований к коррозии
      const minElements: Record<string, number> = {}
      const maxElements: Record<string, number> = {}

      if (formData.corrosionRequirement === 'medium') {
        minElements['Cr'] = 5  // Минимум 5% хрома для средней коррозионной стойкости
      } else if (formData.corrosionRequirement === 'high') {
        minElements['Cr'] = 12  // Минимум 12% для нержавеющей стали
        minElements['Ni'] = 8   // Никель для аустенитной структуры
      }

      const response = await optimizeComposition({
        target_properties: targetProperties,
        constraints: {
          base_element: formData.baseElement,
          forbidden_elements: [],
          max_cost: formData.maxCost,
          min_elements: minElements,
          max_elements: maxElements,
        },
        num_alternatives: 5,
      })

      setResult(response)
    } catch (e: any) {
      const detail = e.response?.data?.detail
      if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError('Ошибка при оптимизации состава')
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Левая панель - форма */}
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-6 flex items-center gap-2">
            <Target className="w-5 h-5 text-blue-600" />
            Оптимизация состава сплава
          </h2>

          <p className="text-gray-600 mb-6">
            Задайте целевые свойства, и алгоритм дифференциальной эволюции
            подберёт оптимальный химический состав.
          </p>

          {/* Целевые свойства */}
          <div className="mb-6">
            <h3 className="font-medium mb-3 text-gray-800">Целевые свойства</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Минимальный предел текучести (МПа)
                </label>
                <input
                  type="number"
                  value={formData.minYieldStrength}
                  onChange={(e) => handleInputChange('minYieldStrength', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="400"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Минимальный предел прочности (МПа)
                </label>
                <input
                  type="number"
                  value={formData.minTensileStrength}
                  onChange={(e) => handleInputChange('minTensileStrength', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="600"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Минимальное удлинение (%)
                </label>
                <input
                  type="number"
                  value={formData.minElongation}
                  onChange={(e) => handleInputChange('minElongation', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="15"
                />
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Целевая твёрдость (HRC) - опционально
                </label>
                <input
                  type="number"
                  value={formData.targetHardness}
                  onChange={(e) => handleInputChange('targetHardness', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="30"
                />
              </div>
            </div>
          </div>

          {/* Ограничения */}
          <div className="mb-6">
            <h3 className="font-medium mb-3 text-gray-800">Ограничения</h3>
            <div className="space-y-3">
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Базовый элемент
                </label>
                <select
                  value={formData.baseElement}
                  onChange={(e) => handleInputChange('baseElement', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="Fe">Железо (Fe) - стали</option>
                  <option value="Al">Алюминий (Al) - лёгкие сплавы</option>
                  <option value="Ti">Титан (Ti) - жаропрочные</option>
                  <option value="Ni">Никель (Ni) - суперсплавы</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Максимальная стоимость
                </label>
                <select
                  value={formData.maxCost}
                  onChange={(e) => handleInputChange('maxCost', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="low">Низкая (Fe, C, Si, Mn)</option>
                  <option value="medium">Средняя (+ немного Cr, Ni)</option>
                  <option value="high">Высокая (любые элементы)</option>
                </select>
              </div>
              <div>
                <label className="block text-sm text-gray-600 mb-1">
                  Требования к коррозионной стойкости
                </label>
                <select
                  value={formData.corrosionRequirement}
                  onChange={(e) => handleInputChange('corrosionRequirement', e.target.value)}
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Не важна</option>
                  <option value="medium">Средняя (Cr 5%)</option>
                  <option value="high">Высокая - нержавеющая (Cr 12%, Ni 8%)</option>
                </select>
              </div>
            </div>
          </div>

          <button
            onClick={handleOptimize}
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2 transition-colors"
          >
            {loading ? (
              <>
                <Loader2 className="w-5 h-5 animate-spin" />
                Оптимизация... (может занять 10-30 сек)
              </>
            ) : (
              <>
                <Target className="w-5 h-5" />
                Подобрать оптимальный состав
              </>
            )}
          </button>
        </div>

        {/* Правая панель - результаты */}
        <div>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-4 flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
              <div>
                <p className="font-medium text-red-800">Ошибка</p>
                <p className="text-sm text-red-600">{error}</p>
              </div>
            </div>
          )}

          {result && (
            <div className="space-y-4">
              {/* Оптимальный состав */}
              <div className="bg-white rounded-xl shadow-sm border p-6">
                <h3 className="font-semibold mb-4 flex items-center gap-2">
                  <CheckCircle className="w-5 h-5 text-green-600" />
                  Оптимальный состав
                  <span className="ml-auto text-sm font-normal text-gray-500">
                    Соответствие: {(result.fitness_score * 100).toFixed(0)}%
                  </span>
                </h3>

                {/* Состав */}
                <div className="bg-blue-50 rounded-lg p-4 mb-4">
                  <p className="text-sm text-blue-600 mb-2">Химический состав:</p>
                  <p className="font-mono text-sm">
                    {formatComposition(result.optimal_composition)}
                  </p>
                </div>

                {/* Прогнозируемые свойства */}
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Предел текучести</p>
                    <p className="text-lg font-bold text-gray-900">
                      {result.predicted_properties.yield_strength_mpa} МПа
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Предел прочности</p>
                    <p className="text-lg font-bold text-gray-900">
                      {result.predicted_properties.tensile_strength_mpa} МПа
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Удлинение</p>
                    <p className="text-lg font-bold text-gray-900">
                      {result.predicted_properties.elongation_percent}%
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Твёрдость</p>
                    <p className="text-lg font-bold text-gray-900">
                      {result.predicted_properties.hardness_hrc
                        ? `${result.predicted_properties.hardness_hrc} HRC`
                        : 'N/A'}
                    </p>
                  </div>
                </div>
              </div>

              {/* Альтернативы */}
              {result.alternatives.length > 0 && (
                <div className="bg-white rounded-xl shadow-sm border p-6">
                  <h3 className="font-semibold mb-4 flex items-center gap-2">
                    <Beaker className="w-5 h-5 text-purple-600" />
                    Альтернативные составы ({result.alternatives.length})
                  </h3>

                  <div className="space-y-3">
                    {result.alternatives.map((alt, index) => (
                      <div
                        key={index}
                        className="border rounded-lg p-3 hover:bg-gray-50 transition-colors"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <span className="text-sm font-medium text-gray-700">
                            Вариант {index + 1}
                          </span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-gray-500">
                              Соответствие: {(alt.fitness_score * 100).toFixed(0)}%
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded-full flex items-center gap-1 ${
                              alt.cost_level === 'low'
                                ? 'bg-green-100 text-green-700'
                                : alt.cost_level === 'medium'
                                ? 'bg-yellow-100 text-yellow-700'
                                : 'bg-red-100 text-red-700'
                            }`}>
                              <DollarSign className="w-3 h-3" />
                              {COST_LABELS[alt.cost_level] || alt.cost_level}
                            </span>
                          </div>
                        </div>
                        <p className="text-xs font-mono text-gray-600 mb-2">
                          {formatComposition(alt.composition)}
                        </p>
                        <div className="flex gap-4 text-xs text-gray-500">
                          <span>YS: {alt.predicted_properties.yield_strength_mpa} МПа</span>
                          <span>TS: {alt.predicted_properties.tensile_strength_mpa} МПа</span>
                          <span>El: {alt.predicted_properties.elongation_percent}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {!result && !error && (
            <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-500">
              <Target className="w-12 h-12 mx-auto mb-4 text-gray-300" />
              <p className="mb-2">Задайте целевые свойства и нажмите "Подобрать"</p>
              <p className="text-sm text-gray-400">
                Алгоритм найдёт оптимальный химический состав,
                соответствующий вашим требованиям
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
