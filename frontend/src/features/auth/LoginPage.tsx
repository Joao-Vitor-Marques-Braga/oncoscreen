import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Activity, Lock, ShieldCheck, Stethoscope, User } from "lucide-react";
import { apiClient } from "@/shared/api/client";
import { useAuth } from "@/shared/context/AuthContext";
import { Button, Card } from "@/shared/components/ui";
import type { AuthUser } from "@/shared/types/clinical";

const loginSchema = z.object({
  identifier: z.string().min(3, "Informe seu e-mail ou CPF válido."),
  password: z.string().min(3, "Informe a senha."),
});

type LoginFormValues = z.infer<typeof loginSchema>;

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [profileTab, setProfileTab] = useState<"DOCTOR" | "PATIENT">("DOCTOR");
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { identifier: "", password: "" },
  });

  const handleTabSwitch = (tab: "DOCTOR" | "PATIENT") => {
    setProfileTab(tab);
    setErrorMsg(null);
    setValue("identifier", "");
    setValue("password", "");
  };

  const onSubmit = async (values: LoginFormValues) => {
    setErrorMsg(null);
    try {
      const resp = await apiClient.post<AuthUser>("/auth/login", values);
      login(resp.data);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "Não foi possível autenticar. Verifique suas credenciais.";
      setErrorMsg(detail);
    }
  };

  return (
    <div className="min-h-screen bg-[#F8FAFC] dark:bg-[#0B1120] flex flex-col justify-center items-center px-4 py-8">
      <div className="w-full max-w-md space-y-6">
        {/* Institutional Brand */}
        <div className="text-center space-y-2">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-md bg-[#1E3A8A] text-white">
            <Activity className="w-7 h-7" />
          </div>
          <h1 className="text-2xl font-bold text-[#0F172A] dark:text-white tracking-tight">
            OncoScreen.AI
          </h1>
          <p className="text-xs text-[#475569] dark:text-[#94A3B8]">
            OralCare-Vision CDSS • Triagem Multimodal de Câncer de Cabeça e Pescoço
          </p>
        </div>

        <Card className="overflow-hidden">
          {/* Profile Selector Tabs */}
          <div className="grid grid-cols-2 border-b border-[#CBD5E1] dark:border-[#334155]">
            <button
              type="button"
              onClick={() => handleTabSwitch("DOCTOR")}
              className={`flex items-center justify-center gap-2 py-3 text-xs font-semibold border-r border-[#CBD5E1] dark:border-[#334155] transition-colors ${
                profileTab === "DOCTOR"
                  ? "bg-[#1E3A8A] text-white"
                  : "bg-[#F8FAFC] dark:bg-[#1E293B] text-[#475569] dark:text-[#94A3B8]"
              }`}
            >
              <Stethoscope className="w-4 h-4" />
              Acesso Médico
            </button>
            <button
              type="button"
              onClick={() => handleTabSwitch("PATIENT")}
              className={`flex items-center justify-center gap-2 py-3 text-xs font-semibold transition-colors ${
                profileTab === "PATIENT"
                  ? "bg-[#1E3A8A] text-white"
                  : "bg-[#F8FAFC] dark:bg-[#1E293B] text-[#475569] dark:text-[#94A3B8]"
              }`}
            >
              <User className="w-4 h-4" />
              Portal do Paciente
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
            {errorMsg && (
              <div className="p-3 text-xs font-medium bg-[#FEF2F2] text-[#991B1B] border border-[#FCA5A5] rounded">
                {errorMsg}
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#E2E8F0] mb-1">
                {profileTab === "DOCTOR" ? "E-mail Institucional" : "CPF do Paciente"}
              </label>
              <input
                type="text"
                placeholder={
                  profileTab === "DOCTOR" ? "doutor@oncoscreen.ai" : "000.000.000-00"
                }
                {...register("identifier")}
                className="w-full px-3 py-2 text-sm bg-white dark:bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md focus:outline-none focus:border-[#1E3A8A]"
              />
              {errors.identifier && (
                <p className="text-xs text-[#B91C1C] mt-1">{errors.identifier.message}</p>
              )}
            </div>

            <div>
              <label className="block text-xs font-semibold text-[#0F172A] dark:text-[#E2E8F0] mb-1">
                Senha
              </label>
              <div className="relative">
                <input
                  type="password"
                  placeholder={profileTab === "DOCTOR" ? "••••••••" : "Data nasc. (DDMMAAAA)"}
                  {...register("password")}
                  className="w-full px-3 py-2 text-sm bg-white dark:bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md focus:outline-none focus:border-[#1E3A8A]"
                />
                <Lock className="w-4 h-4 text-[#94A3B8] absolute right-3 top-2.5" />
              </div>
              {errors.password && (
                <p className="text-xs text-[#B91C1C] mt-1">{errors.password.message}</p>
              )}
            </div>

            <Button type="submit" disabled={isSubmitting} className="w-full">
              {isSubmitting ? "Autenticando..." : "Entrar no Sistema"}
            </Button>

            {profileTab === "DOCTOR" ? (
              <div className="pt-2 border-t border-[#E2E8F0] dark:border-[#334155] text-[11px] text-[#475569] dark:text-[#94A3B8] flex items-center justify-between">
                <span>Credencial inicial (seed):</span>
                <button
                  type="button"
                  onClick={() => {
                    setValue("identifier", "doutor@oncoscreen.ai");
                    setValue("password", "admin123");
                  }}
                  className="font-mono text-[#1E3A8A] dark:text-[#93C5FD] underline"
                >
                  doutor@oncoscreen.ai / admin123
                </button>
              </div>
            ) : (
              <div className="pt-2 border-t border-[#E2E8F0] dark:border-[#334155] text-[11px] text-[#475569] dark:text-[#94A3B8] flex items-start gap-1.5">
                <ShieldCheck className="w-4 h-4 text-[#059669] shrink-0 mt-0.5" />
                <span>
                  O acesso do paciente é cadastrado pelo médico durante a triagem. Senha inicial padrão: data de nascimento (DDMMAAAA).
                </span>
              </div>
            )}
          </form>
        </Card>
      </div>
    </div>
  );
};

