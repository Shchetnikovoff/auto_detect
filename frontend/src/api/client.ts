/**
 * API клиент для AlloyPredictor
 *
 * Поддерживает эндпоинты:
 * - /predict/quick - быстрый прогноз механических свойств
 * - /predict/full - полный прогноз всех свойств
 * - /predict/fatigue - усталостные свойства
 * - /predict/impact - ударная вязкость
 * - /predict/corrosion - коррозионные свойства
 * - /predict/heat-treatment - термообработка
 * - /predict/wear - износостойкость
 * - /predict/optimize - оптимизация состава
 */

import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
})

// =============================================================================
// ТИПЫ - Химический состав
// =============================================================================

export interface Composition {
  Fe?: number
  C?: number
  Si?: number
  Mn?: number
  Cr?: number
  Ni?: number
  Mo?: number
  V?: number
  W?: number
  Co?: number
  Ti?: number
  Al?: number
  Cu?: number
  Nb?: number
  P?: number
  S?: number
  N?: number
}

export interface MechanicalProperties {
  yield_strength_mpa: number
  tensile_strength_mpa: number
  elongation_percent: number
  hardness_hrc?: number
  hardness_hv?: number
  youngs_modulus_gpa: number
  density_g_cm3?: number
}

export interface AlloyBehavior {
  corrosion_resistance: string
  magnetic: boolean
  weldability: string
  heat_treatable: boolean
  oxidation_resistance?: string
  wear_resistance?: string
}

export interface AlloyClassification {
  alloy_type: string
  grade?: string
  applications: string[]
  similar_alloys: string[]
}

export interface PredictionResponse {
  mechanical_properties: MechanicalProperties
  behavior: AlloyBehavior
  classification: AlloyClassification
  confidence: number
  warnings: string[]
}

export interface SteelGrade {
  grade: string
  standard: string
  composition: Composition
  yield_strength?: number
  tensile_strength?: number
  applications: string[]
  type: string
}

// API функции
export async function predictProperties(composition: Composition): Promise<PredictionResponse> {
  // Фильтруем только непустые значения > 0
  const filtered: Composition = {}
  for (const [key, value] of Object.entries(composition)) {
    if (typeof value === 'number' && !isNaN(value) && value > 0) {
      filtered[key as keyof Composition] = value
    }
  }
  const response = await api.post('/predict/quick', filtered)
  return response.data
}

export async function getSteelGrades(params?: {
  type_filter?: string
  min_strength?: number
  search?: string
}): Promise<SteelGrade[]> {
  const response = await api.get('/reference/grades', { params })
  return response.data
}

export async function getSteelTypes(): Promise<string[]> {
  const response = await api.get('/reference/types')
  return response.data
}

export async function getElements(): Promise<any> {
  const response = await api.get('/predict/elements')
  return response.data
}

// Типы для оптимизации
export interface OptimizationConstraints {
  base_element: string
  forbidden_elements: string[]
  max_cost?: string
  min_elements: Record<string, number>
  max_elements: Record<string, number>
}

export interface OptimizationRequest {
  target_properties: {
    min_yield_strength?: number
    min_tensile_strength?: number
    min_elongation?: number
    target_hardness?: number
  }
  constraints: OptimizationConstraints
  num_alternatives: number
}

export interface OptimizationAlternative {
  composition: Composition
  predicted_properties: {
    yield_strength_mpa: number
    tensile_strength_mpa: number
    elongation_percent: number
    hardness_hrc?: number
  }
  fitness_score: number
  cost_level: string
}

export interface OptimizationResponse {
  optimal_composition: Composition
  predicted_properties: MechanicalProperties
  fitness_score: number
  alternatives: OptimizationAlternative[]
}

// API функция оптимизации состава
export async function optimizeComposition(request: OptimizationRequest): Promise<OptimizationResponse> {
  const response = await api.post('/predict/optimize', request)
  return response.data
}

// =============================================================================
// РАСШИРЕННЫЕ ТИПЫ - Дополнительные свойства сплавов
// =============================================================================

/** Усталостные свойства */
export interface FatigueProperties {
  fatigue_limit_mpa: number
  fatigue_ratio: number
  cycles_to_failure_log?: number
  basquin_exponent?: number
  endurance_limit_cycles: number
}

/** Ударная вязкость */
export interface ImpactProperties {
  impact_energy_j: number
  kcv_j_cm2: number
  transition_temp_c: number
  upper_shelf_energy_j?: number
  lower_shelf_energy_j?: number
  ductile_fraction_percent?: number
}

/** Коррозионные свойства */
export interface CorrosionProperties {
  pren: number
  cpt_c?: number
  corrosion_rate_mm_year: number
  passivation_potential_v?: number
  pitting_potential_v?: number
}

/** Свойства термообработки */
export interface HeatTreatmentProperties {
  carbon_equivalent: number
  ac1_temp_c: number
  ac3_temp_c: number
  ms_temp_c: number
  mf_temp_c?: number
  quench_hardness_hrc?: number
  hardenability_mm?: number
  recommended_quench_temp_c?: number
  recommended_temper_temp_c?: number
}

/** Износостойкость */
export interface WearProperties {
  wear_resistance_index: number
  mass_loss_mg?: number
  volume_loss_mm3?: number
  carbide_volume_percent?: number
  abrasion_resistance_class?: string
}

/** Полный ответ со всеми свойствами */
export interface FullPredictionResponse {
  mechanical_properties: MechanicalProperties
  fatigue_properties: FatigueProperties
  impact_properties: ImpactProperties
  corrosion_properties: CorrosionProperties
  heat_treatment_properties: HeatTreatmentProperties
  wear_properties: WearProperties
  behavior: AlloyBehavior
  classification: AlloyClassification
  confidence: number
  warnings: string[]
  models_used: string[]
}

// =============================================================================
// API ФУНКЦИИ - Расширенные эндпоинты
// =============================================================================

/** Полный прогноз всех свойств */
export async function predictFullProperties(composition: Composition): Promise<FullPredictionResponse> {
  const filtered: Composition = {}
  for (const [key, value] of Object.entries(composition)) {
    if (typeof value === 'number' && !isNaN(value) && value > 0) {
      filtered[key as keyof Composition] = value
    }
  }
  const response = await api.post('/predict/full', filtered)
  return response.data
}

/** Прогноз усталостных свойств */
export async function predictFatigue(composition: Composition): Promise<FatigueProperties> {
  const filtered: Composition = {}
  for (const [key, value] of Object.entries(composition)) {
    if (typeof value === 'number' && !isNaN(value) && value > 0) {
      filtered[key as keyof Composition] = value
    }
  }
  const response = await api.post('/predict/fatigue', filtered)
  return response.data
}

/** Прогноз ударной вязкости */
export async function predictImpact(composition: Composition): Promise<ImpactProperties> {
  const filtered: Composition = {}
  for (const [key, value] of Object.entries(composition)) {
    if (typeof value === 'number' && !isNaN(value) && value > 0) {
      filtered[key as keyof Composition] = value
    }
  }
  const response = await api.post('/predict/impact', filtered)
  return response.data
}

/** Прогноз коррозионных свойств */
export async function predictCorrosion(composition: Composition): Promise<CorrosionProperties> {
  const filtered: Composition = {}
  for (const [key, value] of Object.entries(composition)) {
    if (typeof value === 'number' && !isNaN(value) && value > 0) {
      filtered[key as keyof Composition] = value
    }
  }
  const response = await api.post('/predict/corrosion', filtered)
  return response.data
}

/** Прогноз свойств термообработки */
export async function predictHeatTreatment(composition: Composition): Promise<HeatTreatmentProperties> {
  const filtered: Composition = {}
  for (const [key, value] of Object.entries(composition)) {
    if (typeof value === 'number' && !isNaN(value) && value > 0) {
      filtered[key as keyof Composition] = value
    }
  }
  const response = await api.post('/predict/heat-treatment', filtered)
  return response.data
}

/** Прогноз износостойкости */
export async function predictWear(composition: Composition): Promise<WearProperties> {
  const filtered: Composition = {}
  for (const [key, value] of Object.entries(composition)) {
    if (typeof value === 'number' && !isNaN(value) && value > 0) {
      filtered[key as keyof Composition] = value
    }
  }
  const response = await api.post('/predict/wear', filtered)
  return response.data
}

/** Получить статус загруженных моделей */
export async function getModelsStatus(): Promise<{
  loaded_models: string[]
  loaded_categories: string[]
  available_endpoints: Record<string, string>
}> {
  const response = await api.get('/predict/models-status')
  return response.data
}
