import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { CheckCircle2, Search, UserPlus } from "lucide-react";
import { apiClient } from "@/shared/api/client";
import { Button, Card, CardHeader } from "@/shared/components/ui";
import type { PatientSummary } from "@/shared/types/clinical";

export const patientLookupSchema = z.object({
  cpf: z
    .string()
    .transform((v) => v.replace(/\D/g, ""))
    .refine((v) => v.length === 11, "CPF deve conter 11 dígitos."),
  full_name: z.string().optional(),
  birth_date: z.string().optional(),
  phone_whatsapp: z.string().optional(),
});

type PatientFormValues = z.infer<typeof patientLookupSchema>;

interface PatientLookupCardProps {
  selectedPatient: PatientSummary | null;
  onSelectPatient: (patient: PatientSummary) => void;
}

export const PatientLookupCard: React.FC<PatientLookupCardProps> = ({
  selectedPatient,
  onSelectPatient,
}) => {
  const [needsRegistration, setNeedsRegistration] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<PatientFormValues>({
    resolver: zodResolver(patientLookupSchema),
  });

  const onSubmit = async (values: PatientFormValues) => {
    setErrorMsg(null);
    if (needsRegistration) {
      if (!values.full_name || !values.birth_date || !values.phone_whatsapp) {
        setErrorMsg("Preencha Nome Completo, Data de Nascimento e WhatsApp com DDD.");
        return;
      }
    }

    try {
      const payload = needsRegistration
        ? values
        : { cpf: values.cpf };
      const resp = await apiClient.post<PatientSummary>(
        "/patients/lookup-or-register",
        payload
      );
      setNeedsRegistration(false);
      onSelectPatient(resp.data);
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status;
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Erro ao consultar CPF.";
      if (status === 422 && detail.includes("Paciente não encontrado")) {
        setNeedsRegistration(true);
        setErrorMsg("CPF não cadastrado. Preencha os dados mínimos abaixo para criar o prontuário.");
      } else {
        setErrorMsg(detail);
      }
    }
  };

  return (
    <Card>
      <CardHeader
        title="1. Identificação do Paciente por CPF"
        subtitle="Busque o paciente pelo CPF ou realize o cadastro rápido para iniciar a triagem."
        right={
          selectedPatient && (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-[#065F46] bg-[#ECFDF5] border border-[#6EE7B7] px-2.5 py-1 rounded">
              <CheckCircle2 className="w-3.5 h-3.5" />
              Paciente Selecionado
            </span>
          )
        }
      />

      <div className="p-4 space-y-4">
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="flex flex-col sm:flex-row gap-3 items-start sm:items-end">
            <div className="flex-1 w-full">
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#E2E8F0] mb-1">
                CPF do Paciente
              </label>
              <input
                type="text"
                placeholder="000.000.000-00"
                {...register("cpf")}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md"
              />
              {errors.cpf && (
                <p className="text-xs text-[#B91C1C] mt-1">{errors.cpf.message}</p>
              )}
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full sm:w-auto">
              {needsRegistration ? (
                <>
                  <UserPlus className="w-4 h-4" />
                  Cadastrar e Selecionar
                </>
              ) : (
                <>
                  <Search className="w-4 h-4" />
                  Buscar CPF
                </>
              )}
            </Button>
          </div>

          {needsRegistration && (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 p-3 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md">
              <div>
                <label className="block text-xs font-semibold mb-1">Nome Completo</label>
                <input
                  type="text"
                  placeholder="Ex.: Maria Aparecida Souza"
                  {...register("full_name")}
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Data de Nascimento</label>
                <input
                  type="date"
                  {...register("birth_date")}
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md"
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-1">Telefone / WhatsApp (DDD)</label>
                <input
                  type="text"
                  placeholder="11999998888"
                  {...register("phone_whatsapp")}
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md"
                />
              </div>
            </div>
          )}

          {errorMsg && (
            <div className="p-2.5 text-xs bg-[#FFFBEB] text-[#92400E] border border-[#FCD34D] rounded">
              {errorMsg}
            </div>
          )}
        </form>

        {selectedPatient && (
          <div className="p-3 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md flex flex-wrap items-center justify-between gap-3 text-xs">
            <div className="space-y-0.5">
              <div className="font-bold text-sm text-[#0F172A] dark:text-white">
                {selectedPatient.full_name}
              </div>
              <div className="text-[#475569] dark:text-[#94A3B8]">
                CPF: <span className="font-mono">{selectedPatient.cpf_formatted}</span> •
                WhatsApp: {selectedPatient.phone_whatsapp} • Exames anteriores:{" "}
                <strong>{selectedPatient.exam_count}</strong>
              </div>
              {selectedPatient.initial_patient_password_hint && (
                <div className="text-[#065F46] dark:text-[#6EE7B7] font-medium">
                  Conta do paciente criada ({selectedPatient.initial_patient_password_hint})
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </Card>
  );
};

