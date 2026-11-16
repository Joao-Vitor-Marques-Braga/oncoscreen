import { z } from "zod";
import type { AnamnesisData } from "@/shared/types/clinical";

export const anamnesisSchema = z.object({
  active_smoking: z.boolean().default(false),
  former_smoker: z.boolean().default(false),
  frequent_alcohol: z.boolean().default(false),
  chronic_sun_exposure: z.boolean().default(false),
  family_cancer_history: z.boolean().default(false),

  evolution_gt_14_days: z.boolean().default(false),
  non_healing_ulcer: z.boolean().default(false),
  leukoplakia: z.boolean().default(false),
  erythroplakia: z.boolean().default(false),
  induration_raised_borders: z.boolean().default(false),
  spontaneous_or_touch_bleeding: z.boolean().default(false),

  local_pain: z.boolean().default(false),
  odynophagia: z.boolean().default(false),
  dysphagia: z.boolean().default(false),
  cervical_lymphadenopathy: z.boolean().default(false),
  recent_weight_loss: z.boolean().default(false),

  clinical_notes: z.string().max(1000, "Máximo de 1000 caracteres.").default(""),
});

export type AnamnesisFormValues = z.infer<typeof anamnesisSchema>;

export const ANAMNESIS_GROUPS: {
  title: string;
  items: { key: keyof Omit<AnamnesisData, "clinical_notes">; label: string; highlight?: boolean }[];
}[] = [
  {
    title: "Fatores de Risco",
    items: [
      { key: "active_smoking", label: "Tabagismo ativo", highlight: true },
      { key: "former_smoker", label: "Ex-tabagista" },
      { key: "frequent_alcohol", label: "Etilismo frequente" },
      { key: "chronic_sun_exposure", label: "Exposição solar crônica (lábio)" },
      { key: "family_cancer_history", label: "Histórico familiar de câncer" },
    ],
  },
  {
    title: "Características da Lesão",
    items: [
      { key: "evolution_gt_14_days", label: "Evolução > 14 dias (Regra SUS)", highlight: true },
      { key: "non_healing_ulcer", label: "Úlcera que não cicatriza" },
      { key: "leukoplakia", label: "Mancha branca (Leucoplasia)" },
      { key: "erythroplakia", label: "Mancha vermelha (Eritroplasia)", highlight: true },
      { key: "induration_raised_borders", label: "Endurecimento / Bordas elevadas", highlight: true },
      { key: "spontaneous_or_touch_bleeding", label: "Sangramento espontâneo ou ao toque" },
    ],
  },
  {
    title: "Sintomas Associados",
    items: [
      { key: "local_pain", label: "Dor local" },
      { key: "odynophagia", label: "Odinofagia (dor ao engolir)" },
      { key: "dysphagia", label: "Disfagia" },
      { key: "cervical_lymphadenopathy", label: "Linfonodomegalia cervical palpável" },
      { key: "recent_weight_loss", label: "Perda de peso recente" },
    ],
  },
];

