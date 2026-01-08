/**
 * Страница прогнозирования свойств сплава
 *
 * Поддерживает два режима:
 * - Быстрый прогноз: базовые механические свойства
 * - Полный прогноз: все категории свойств (усталость, удар, коррозия, термообработка, износ)
 */
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import {
  Beaker, Loader2, AlertCircle, CheckCircle, Magnet, Droplets, Flame, Wrench,
  Zap, Thermometer, Shield, Activity, Gauge, ChevronDown, ChevronUp
} from 'lucide-react'
import {
  predictProperties, predictFullProperties,
  Composition, PredictionResponse, FullPredictionResponse
} from '../api/client'

const ELEMENTS = [
  { symbol: 'Fe', name: 'Железо', max: 100 },
  { symbol: 'C', name: 'Углерод', max: 5 },
  { symbol: 'Si', name: 'Кремний', max: 5 },
  { symbol: 'Mn', name: 'Марганец', max: 20 },
  { symbol: 'Cr', name: 'Хром', max: 30 },
  { symbol: 'Ni', name: 'Никель', max: 40 },
  { symbol: 'Mo', name: 'Молибден', max: 10 },
  { symbol: 'V', name: 'Ванадий', max: 5 },
  { symbol: 'W', name: 'Вольфрам', max: 20 },
  { symbol: 'Ti', name: 'Титан', max: 5 },
  { symbol: 'Al', name: 'Алюминий', max: 100 },
  { symbol: 'Cu', name: 'Медь', max: 10 },
]

// Компонент секции результатов (сворачиваемый)
function ResultSection({
  title, icon, children, defaultOpen = true, color = 'blue'
}: {
  title: string
  icon: React.ReactNode
  children: React.ReactNode
  defaultOpen?: boolean
  color?: 'blue' | 'green' | 'purple' | 'orange' | 'red' | 'cyan'
}) {
  const [isOpen, setIsOpen] = useState(defaultOpen)

  const colorClasses = {
    blue: 'text-blue-600 bg-blue-50',
    green: 'text-green-600 bg-green-50',
    purple: 'text-purple-600 bg-purple-50',
    orange: 'text-orange-600 bg-orange-50',
    red: 'text-red-600 bg-red-50',
    cyan: 'text-cyan-600 bg-cyan-50',
  }

  return (
    <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-6 py-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
      >
        <h3 className="font-semibold flex items-center gap-2">
          <span className={`p-1.5 rounded-lg ${colorClasses[color]}`}>
            {icon}
          </span>
          {title}
        </h3>
        {isOpen ? <ChevronUp className="w-5 h-5 text-gray-400" /> : <ChevronDown className="w-5 h-5 text-gray-400" />}
      </button>
      {isOpen && <div className="px-6 pb-6">{children}</div>}
    </div>
  )
}

// Карточка со значением свойства
function PropertyCard({
  label, value, unit, highlight = false, size = 'normal'
}: {
  label: string
  value: string | number | undefined | null
  unit?: string
  highlight?: boolean
  size?: 'normal' | 'large'
}) {
  if (value === undefined || value === null) return null

  return (
    <div className={`rounded-lg p-4 ${highlight ? 'bg-blue-50' : 'bg-gray-50'}`}>
      <p className={`text-sm ${highlight ? 'text-blue-600' : 'text-gray-600'}`}>{label}</p>
      <p className={`font-bold ${highlight ? 'text-blue-900' : 'text-gray-900'} ${size === 'large' ? 'text-2xl' : 'text-xl'}`}>
        {typeof value === 'number' ? value.toFixed(1) : value}
        {unit && <span className="text-sm font-normal ml-1">{unit}</span>}
      </p>
    </div>
  )
}

export default function PredictPage() {
  const { register, handleSubmit, watch, setValue } = useForm<Composition>({
    defaultValues: { Fe: 97.5, C: 0.45, Si: 0.25, Mn: 0.65 }
  })
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<PredictionResponse | null>(null)
  const [fullResult, setFullResult] = useState<FullPredictionResponse | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [mode, setMode] = useState<'quick' | 'full'>('quick')

  const values = watch()
  const total = Object.values(values).reduce((sum, v) => sum + (Number(v) || 0), 0)

  const onSubmit = async (data: Composition) => {
    setLoading(true)
    setError(null)
    setResult(null)
    setFullResult(null)

    try {
      if (mode === 'full') {
        const response = await predictFullProperties(data)
        setFullResult(response)
      } else {
        const response = await predictProperties(data)
        setResult(response)
      }
    } catch (e: any) {
      const detail = e.response?.data?.detail
      if (Array.isArray(detail)) {
        setError(detail.map((d: any) => d.msg || JSON.stringify(d)).join(', '))
      } else if (typeof detail === 'string') {
        setError(detail)
      } else {
        setError('Ошибка при прогнозировании')
      }
    } finally {
      setLoading(false)
    }
  }

  const loadPreset = (preset: Composition) => {
    Object.entries(preset).forEach(([key, value]) => {
      setValue(key as keyof Composition, value)
    })
  }

  // Используем либо полный результат, либо базовый
  const activeResult = fullResult || result

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
      {/* Левая панель - ввод состава */}
      <div>
        <div className="bg-white rounded-xl shadow-sm border p-6">
          <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
            <Beaker className="w-5 h-5 text-blue-600" />
            Химический состав сплава
          </h2>

          {/* Переключатель режима */}
          <div className="mb-4 p-1 bg-gray-100 rounded-lg inline-flex">
            <button
              type="button"
              onClick={() => setMode('quick')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                mode === 'quick'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Быстрый прогноз
            </button>
            <button
              type="button"
              onClick={() => setMode('full')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-colors ${
                mode === 'full'
                  ? 'bg-white text-blue-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Полный анализ
            </button>
          </div>

          {mode === 'full' && (
            <p className="text-xs text-gray-500 mb-4">
              Полный анализ включает: усталость, ударную вязкость, коррозию, термообработку, износостойкость
            </p>
          )}

          {/* Пресеты */}
          <div className="mb-4">
            <p className="text-sm text-gray-500 mb-2">Быстрый выбор:</p>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => loadPreset({ Fe: 97.5, C: 0.45, Si: 0.25, Mn: 0.65 })}
                className="px-3 py-1 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Сталь 45
              </button>
              <button
                type="button"
                onClick={() => loadPreset({ Fe: 68, C: 0.12, Si: 0.8, Mn: 2, Cr: 18, Ni: 10, Ti: 0.8 })}
                className="px-3 py-1 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                12Х18Н10Т
              </button>
              <button
                type="button"
                onClick={() => loadPreset({ Fe: 96.8, C: 0.4, Si: 0.25, Mn: 0.65, Cr: 1 })}
                className="px-3 py-1 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                40Х
              </button>
              <button
                type="button"
                onClick={() => loadPreset({ Fe: 97, C: 0.12, Si: 0.7, Mn: 1.5 })}
                className="px-3 py-1 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                09Г2С
              </button>
              <button
                type="button"
                onClick={() => loadPreset({ Fe: 84, C: 0.95, Si: 0.3, Mn: 0.35, Cr: 4, Mo: 5, V: 2, W: 6 })}
                className="px-3 py-1 text-sm bg-gray-100 rounded-lg hover:bg-gray-200"
              >
                Р6М5 (быстрорез)
              </button>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)}>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
              {ELEMENTS.map((elem) => (
                <div key={elem.symbol} className="relative">
                  <label className="block text-xs text-gray-500 mb-1">
                    {elem.symbol} - {elem.name}
                  </label>
                  <input
                    type="number"
                    step="0.01"
                    min="0"
                    max={elem.max}
                    {...register(elem.symbol as keyof Composition, { valueAsNumber: true })}
                    className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="0"
                  />
                  <span className="absolute right-3 top-7 text-gray-400 text-sm">%</span>
                </div>
              ))}
            </div>

            {/* Сумма */}
            <div className={`mt-4 p-3 rounded-lg ${Math.abs(total - 100) > 5 ? 'bg-yellow-50 border border-yellow-200' : 'bg-green-50 border border-green-200'}`}>
              <div className="flex items-center justify-between">
                <span className="text-sm">Сумма компонентов:</span>
                <span className={`font-semibold ${Math.abs(total - 100) > 5 ? 'text-yellow-700' : 'text-green-700'}`}>
                  {total.toFixed(2)}%
                </span>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="mt-4 w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  {mode === 'full' ? 'Полный анализ...' : 'Анализ...'}
                </>
              ) : (
                <>
                  <Beaker className="w-5 h-5" />
                  {mode === 'full' ? 'Полный анализ свойств' : 'Прогнозировать свойства'}
                </>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* Правая панель - результаты */}
      <div className="space-y-4">
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Ошибка</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
        )}

        {activeResult && (
          <>
            {/* Механические свойства */}
            <ResultSection
              title="Механические свойства"
              icon={<CheckCircle className="w-4 h-4" />}
              color="blue"
            >
              <div className="flex items-center gap-2 mb-4">
                <span className="text-sm text-gray-500">
                  Уверенность: {(activeResult.confidence * 100).toFixed(0)}%
                </span>
                <div className="flex-1 h-2 bg-gray-200 rounded-full">
                  <div
                    className="h-2 bg-blue-500 rounded-full"
                    style={{ width: `${activeResult.confidence * 100}%` }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <PropertyCard
                  label="Предел текучести"
                  value={activeResult.mechanical_properties.yield_strength_mpa}
                  unit="МПа"
                  highlight
                  size="large"
                />
                <PropertyCard
                  label="Предел прочности"
                  value={activeResult.mechanical_properties.tensile_strength_mpa}
                  unit="МПа"
                  highlight
                  size="large"
                />
                <PropertyCard
                  label="Удлинение"
                  value={activeResult.mechanical_properties.elongation_percent}
                  unit="%"
                />
                <PropertyCard
                  label="Твёрдость"
                  value={activeResult.mechanical_properties.hardness_hrc}
                  unit="HRC"
                />
                <PropertyCard
                  label="Модуль Юнга"
                  value={activeResult.mechanical_properties.youngs_modulus_gpa}
                  unit="ГПа"
                />
                <PropertyCard
                  label="Плотность"
                  value={activeResult.mechanical_properties.density_g_cm3}
                  unit="г/см³"
                />
              </div>
            </ResultSection>

            {/* Расширенные свойства (только для полного анализа) */}
            {fullResult && (
              <>
                {/* Усталостные свойства */}
                <ResultSection
                  title="Усталостные свойства"
                  icon={<Activity className="w-4 h-4" />}
                  color="purple"
                  defaultOpen={false}
                >
                  <div className="grid grid-cols-2 gap-3">
                    <PropertyCard
                      label="Предел усталости"
                      value={fullResult.fatigue_properties.fatigue_limit_mpa}
                      unit="МПа"
                      highlight
                    />
                    <PropertyCard
                      label="Коэффициент усталости"
                      value={fullResult.fatigue_properties.fatigue_ratio}
                    />
                    <PropertyCard
                      label="Циклов до разрушения (log)"
                      value={fullResult.fatigue_properties.cycles_to_failure_log}
                    />
                    <PropertyCard
                      label="Экспонента Basquin"
                      value={fullResult.fatigue_properties.basquin_exponent}
                    />
                  </div>
                  <p className="mt-3 text-xs text-gray-500">
                    Предел выносливости при N = {fullResult.fatigue_properties.endurance_limit_cycles?.toExponential(0) || '10⁷'} циклов
                  </p>
                </ResultSection>

                {/* Ударная вязкость */}
                <ResultSection
                  title="Ударная вязкость"
                  icon={<Zap className="w-4 h-4" />}
                  color="orange"
                  defaultOpen={false}
                >
                  <div className="grid grid-cols-2 gap-3">
                    <PropertyCard
                      label="Ударная работа"
                      value={fullResult.impact_properties.impact_energy_j}
                      unit="Дж"
                      highlight
                    />
                    <PropertyCard
                      label="KCV"
                      value={fullResult.impact_properties.kcv_j_cm2}
                      unit="Дж/см²"
                      highlight
                    />
                    <PropertyCard
                      label="Температура перехода"
                      value={fullResult.impact_properties.transition_temp_c}
                      unit="°C"
                    />
                    <PropertyCard
                      label="Верхний порог энергии"
                      value={fullResult.impact_properties.upper_shelf_energy_j}
                      unit="Дж"
                    />
                  </div>
                  {fullResult.impact_properties.ductile_fraction_percent && (
                    <p className="mt-3 text-xs text-gray-500">
                      Доля вязкой составляющей: {fullResult.impact_properties.ductile_fraction_percent}%
                    </p>
                  )}
                </ResultSection>

                {/* Коррозионные свойства */}
                <ResultSection
                  title="Коррозионная стойкость"
                  icon={<Shield className="w-4 h-4" />}
                  color="cyan"
                  defaultOpen={false}
                >
                  <div className="grid grid-cols-2 gap-3">
                    <PropertyCard
                      label="PREN"
                      value={fullResult.corrosion_properties.pren}
                      highlight
                    />
                    <PropertyCard
                      label="Скорость коррозии"
                      value={fullResult.corrosion_properties.corrosion_rate_mm_year}
                      unit="мм/год"
                    />
                    <PropertyCard
                      label="CPT (критич. темп. питтинга)"
                      value={fullResult.corrosion_properties.cpt_c}
                      unit="°C"
                    />
                    <PropertyCard
                      label="Потенциал питтинга"
                      value={fullResult.corrosion_properties.pitting_potential_v}
                      unit="В"
                    />
                  </div>
                  <p className="mt-3 text-xs text-gray-500">
                    PREN = Cr + 3.3×Mo + 16×N. PREN {'>'} 32 - морская вода, PREN {'>'} 40 - отлично
                  </p>
                </ResultSection>

                {/* Термообработка */}
                <ResultSection
                  title="Параметры термообработки"
                  icon={<Thermometer className="w-4 h-4" />}
                  color="red"
                  defaultOpen={false}
                >
                  <div className="grid grid-cols-2 gap-3">
                    <PropertyCard
                      label="Углеродный эквивалент"
                      value={fullResult.heat_treatment_properties.carbon_equivalent}
                      highlight
                    />
                    <PropertyCard
                      label="Ac1 (начало аустенизации)"
                      value={fullResult.heat_treatment_properties.ac1_temp_c}
                      unit="°C"
                    />
                    <PropertyCard
                      label="Ac3 (полная аустенизация)"
                      value={fullResult.heat_treatment_properties.ac3_temp_c}
                      unit="°C"
                    />
                    <PropertyCard
                      label="Ms (начало мартенсита)"
                      value={fullResult.heat_treatment_properties.ms_temp_c}
                      unit="°C"
                    />
                    <PropertyCard
                      label="Твёрдость после закалки"
                      value={fullResult.heat_treatment_properties.quench_hardness_hrc}
                      unit="HRC"
                    />
                    <PropertyCard
                      label="Прокаливаемость"
                      value={fullResult.heat_treatment_properties.hardenability_mm}
                      unit="мм"
                    />
                  </div>
                  {fullResult.heat_treatment_properties.recommended_quench_temp_c && (
                    <div className="mt-3 p-3 bg-orange-50 rounded-lg">
                      <p className="text-sm text-orange-800">
                        <strong>Рекомендации:</strong> Закалка {fullResult.heat_treatment_properties.recommended_quench_temp_c}°C
                        {fullResult.heat_treatment_properties.recommended_temper_temp_c &&
                          ` → Отпуск ${fullResult.heat_treatment_properties.recommended_temper_temp_c}°C`}
                      </p>
                    </div>
                  )}
                </ResultSection>

                {/* Износостойкость */}
                <ResultSection
                  title="Износостойкость"
                  icon={<Gauge className="w-4 h-4" />}
                  color="green"
                  defaultOpen={false}
                >
                  <div className="grid grid-cols-2 gap-3">
                    <PropertyCard
                      label="Индекс износостойкости"
                      value={fullResult.wear_properties.wear_resistance_index}
                      highlight
                    />
                    <PropertyCard
                      label="Потеря массы"
                      value={fullResult.wear_properties.mass_loss_mg}
                      unit="мг"
                    />
                    <PropertyCard
                      label="Потеря объёма"
                      value={fullResult.wear_properties.volume_loss_mm3}
                      unit="мм³"
                    />
                    <PropertyCard
                      label="Объём карбидов"
                      value={fullResult.wear_properties.carbide_volume_percent}
                      unit="%"
                    />
                  </div>
                  {fullResult.wear_properties.abrasion_resistance_class && (
                    <p className="mt-3 text-sm">
                      Класс абразивной стойкости: <strong>{fullResult.wear_properties.abrasion_resistance_class}</strong>
                    </p>
                  )}
                </ResultSection>

                {/* Использованные модели */}
                {fullResult.models_used && fullResult.models_used.length > 0 && (
                  <div className="bg-gray-50 rounded-xl p-4">
                    <p className="text-sm text-gray-500 mb-2">Использованные модели:</p>
                    <div className="flex flex-wrap gap-2">
                      {fullResult.models_used.map((model, i) => (
                        <span key={i} className="px-2 py-1 bg-white border rounded text-xs text-gray-600">
                          {model}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            )}

            {/* Поведение */}
            <ResultSection
              title="Характеристики поведения"
              icon={<Wrench className="w-4 h-4" />}
              color="orange"
              defaultOpen={!fullResult}
            >
              <div className="grid grid-cols-2 gap-3">
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Droplets className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-xs text-gray-500">Коррозионная стойкость</p>
                    <p className="font-medium capitalize">{activeResult.behavior.corrosion_resistance}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Magnet className="w-5 h-5 text-purple-500" />
                  <div>
                    <p className="text-xs text-gray-500">Магнитные свойства</p>
                    <p className="font-medium">{activeResult.behavior.magnetic ? 'Магнитный' : 'Немагнитный'}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Wrench className="w-5 h-5 text-orange-500" />
                  <div>
                    <p className="text-xs text-gray-500">Свариваемость</p>
                    <p className="font-medium capitalize">{activeResult.behavior.weldability}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                  <Flame className="w-5 h-5 text-red-500" />
                  <div>
                    <p className="text-xs text-gray-500">Термообработка</p>
                    <p className="font-medium">{activeResult.behavior.heat_treatable ? 'Возможна' : 'Не требуется'}</p>
                  </div>
                </div>
              </div>
            </ResultSection>

            {/* Классификация */}
            <ResultSection
              title="Классификация и применение"
              icon={<Beaker className="w-4 h-4" />}
              color="green"
              defaultOpen={!fullResult}
            >
              <div className="space-y-3">
                <div>
                  <p className="text-sm text-gray-500">Тип сплава</p>
                  <p className="font-medium">{activeResult.classification.alloy_type.replace(/_/g, ' ')}</p>
                </div>
                {activeResult.classification.grade && (
                  <div>
                    <p className="text-sm text-gray-500">Ближайшая марка</p>
                    <p className="font-medium text-blue-600">{activeResult.classification.grade}</p>
                  </div>
                )}
                <div>
                  <p className="text-sm text-gray-500 mb-2">Области применения</p>
                  <div className="flex flex-wrap gap-2">
                    {activeResult.classification.applications.map((app, i) => (
                      <span key={i} className="px-3 py-1 bg-green-100 text-green-700 rounded-full text-sm">
                        {app}
                      </span>
                    ))}
                  </div>
                </div>
                {activeResult.classification.similar_alloys.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-500 mb-2">Похожие сплавы</p>
                    <div className="flex flex-wrap gap-2">
                      {activeResult.classification.similar_alloys.map((alloy, i) => (
                        <span key={i} className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                          {alloy}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </ResultSection>

            {/* Предупреждения */}
            {activeResult.warnings.length > 0 && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4">
                <p className="font-medium text-yellow-800 mb-2">Предупреждения</p>
                <ul className="list-disc list-inside text-sm text-yellow-700">
                  {activeResult.warnings.map((w, i) => (
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}

        {!activeResult && !error && (
          <div className="bg-white rounded-xl shadow-sm border p-8 text-center text-gray-500">
            <Beaker className="w-12 h-12 mx-auto mb-4 text-gray-300" />
            <p>Введите химический состав сплава и нажмите "Прогнозировать" для получения результатов</p>
            <p className="text-sm mt-2">
              Выберите <strong>Полный анализ</strong> для получения всех свойств: усталость, удар, коррозия, термообработка, износ
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
