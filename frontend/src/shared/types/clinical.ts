export type UserRole = "DOCTOR" | "PATIENT";

export interface AuthUser {
  user_id: string;
  full_name: string;
  role: UserRole;
  patient_id?: string | null;
  access_token: string;
}

export interface PatientSummary {
  id: string;
  cpf_formatted: string;
  cpf_masked: string;
  full_name: string;
  birth_date: string;
  phone_whatsapp: string;
  created_at: string;
  exam_count: number;
  newly_created: boolean;
  initial_patient_password_hint?: string | null;
}

export interface AnamnesisData {
  active_smoking: boolean;
  former_smoker: boolean;
  frequent_alcohol: boolean;
  chronic_sun_exposure: boolean;
  family_cancer_history: boolean;
  evolution_gt_14_days: boolean;
  non_healing_ulcer: boolean;
  leukoplakia: boolean;
  erythroplakia: boolean;
  induration_raised_borders: boolean;
  spontaneous_or_touch_bleeding: boolean;
  local_pain: boolean;
  odynophagia: boolean;
  dysphagia: boolean;
  cervical_lymphadenopathy: boolean;
  recent_weight_loss: boolean;
  clinical_notes: string;
}

export interface GuardrailAssessment {
  clinical_score: number;
  clinical_risk: string;
  cnn_positive: boolean;
  final_risk: string;
  concordance_status: string;
  guardrail_triggered: boolean;
  alert_title: string;
  alert_description: string;
  triggered_red_flags: string[];
}

export interface TriageResult {
  exam_id: string;
  patient_id: string;
  patient_name: string;
  patient_cpf_masked: string;
  cnn_probability: number;
  threshold_used: number;
  anatomical_quadrant: string;
  guardrail: GuardrailAssessment;
  report_markdown: string;
  model_used: string;
  generated_via_fallback: boolean;
  original_image_base64: string;
  gradcam_heatmap_base64: string;
  gradcam_overlay_base64: string;
  inference_time_ms: number;
  created_at: string;
}

export interface ExamListItem {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_cpf_masked: string;
  cnn_probability: number;
  threshold_used: number;
  final_risk: string;
  concordance_status: string;
  anatomical_quadrant: string;
  whatsapp_dispatched: boolean;
  created_at: string;
}

export interface ExamDetail {
  id: string;
  patient_id: string;
  patient_name: string;
  patient_cpf_masked: string;
  patient_phone: string;
  cnn_probability: number;
  threshold_used: number;
  anatomical_quadrant: string;
  anamnesis: AnamnesisData;
  selected_anamnesis_labels: string[];
  guardrail: GuardrailAssessment;
  report_markdown: string;
  model_used: string;
  generated_via_fallback: boolean;
  original_image_base64: string;
  gradcam_heatmap_base64: string;
  gradcam_overlay_base64: string;
  whatsapp_dispatched: boolean;
  created_at: string;
}

export interface SystemMetrics {
  total_exams: number;
  total_patients: number;
  risk_distribution: Record<string, number>;
  concordance_distribution: Record<string, number>;
  guardrail_activations: number;
  average_cnn_probability: number;
  estimated_roc_auc: number;
  estimated_sensitivity: number;
  estimated_specificity: number;
}

export interface SystemStatus {
  default_threshold: number;
  vision: Record<string, unknown>;
  ollama: Record<string, unknown>;
  whatsapp: Record<string, unknown>;
}

