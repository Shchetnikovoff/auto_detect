import { useState, useEffect } from 'react'
import { BookOpen, Search, Loader2 } from 'lucide-react'
import { getSteelGrades, getSteelTypes, SteelGrade } from '../api/client'

export default function ReferencePage() {
  const [grades, setGrades] = useState<SteelGrade[]>([])
  const [types, setTypes] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [search, setSearch] = useState('')
  const [typeFilter, setTypeFilter] = useState('')

  useEffect(() => {
    loadData()
  }, [])

  useEffect(() => {
    loadGrades()
  }, [search, typeFilter])

  const loadData = async () => {
    try {
      const [gradesData, typesData] = await Promise.all([
        getSteelGrades(),
        getSteelTypes()
      ])
      setGrades(gradesData)
      setTypes(typesData)
    } catch (e) {
      console.error('Error loading data:', e)
    } finally {
      setLoading(false)
    }
  }

  const loadGrades = async () => {
    try {
      const params: any = {}
      if (search) params.search = search
      if (typeFilter) params.type_filter = typeFilter
      const data = await getSteelGrades(params)
      setGrades(data)
    } catch (e) {
      console.error('Error loading grades:', e)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    )
  }

  return (
    <div>
      <div className="bg-white rounded-xl shadow-sm border p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-blue-600" />
          Справочник марок сталей
        </h2>

        {/* Фильтры */}
        <div className="flex flex-wrap gap-4">
          <div className="flex-1 min-w-64">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Поиск по марке или применению..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border rounded-lg"
              />
            </div>
          </div>
          <div>
            <select
              value={typeFilter}
              onChange={(e) => setTypeFilter(e.target.value)}
              className="px-4 py-2 border rounded-lg"
            >
              <option value="">Все типы</option>
              {types.map((type) => (
                <option key={type} value={type}>{type}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Таблица марок */}
      <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b">
              <tr>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Марка</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Тип</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">σт (МПа)</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">σв (МПа)</th>
                <th className="px-4 py-3 text-left text-sm font-medium text-gray-600">Применение</th>
              </tr>
            </thead>
            <tbody>
              {grades.map((grade, i) => (
                <tr key={grade.grade} className={i % 2 ? 'bg-gray-50' : ''}>
                  <td className="px-4 py-3">
                    <span className="font-medium text-blue-600">{grade.grade}</span>
                    <span className="ml-2 text-xs text-gray-400">{grade.standard}</span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{grade.type}</td>
                  <td className="px-4 py-3 text-sm">{grade.yield_strength || '—'}</td>
                  <td className="px-4 py-3 text-sm">{grade.tensile_strength || '—'}</td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1">
                      {grade.applications.slice(0, 2).map((app, j) => (
                        <span key={j} className="px-2 py-0.5 bg-gray-100 rounded text-xs text-gray-600">
                          {app}
                        </span>
                      ))}
                      {grade.applications.length > 2 && (
                        <span className="text-xs text-gray-400">+{grade.applications.length - 2}</span>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {grades.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            Марки не найдены
          </div>
        )}
      </div>
    </div>
  )
}
