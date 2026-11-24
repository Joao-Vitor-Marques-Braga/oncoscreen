import React from "react";
import { sanitizeClinicalText } from "@/shared/utils/generateClinicalPdf";

export const Card: React.FC<{
  children: React.ReactNode;
  className?: string;
}> = ({ children, className = "" }) => (
  <div
    className={`bg-white dark:bg-[#111827] border border-[#CBD5E1] dark:border-[#334155] rounded-md ${className}`}
  >
    {children}
  </div>
);

export const CardHeader: React.FC<{
  title: string;
  subtitle?: string;
  right?: React.ReactNode;
}> = ({ title, subtitle, right }) => (
  <div className="px-4 py-3 border-b border-[#CBD5E1] dark:border-[#334155] bg-[#F8FAFC] dark:bg-[#1E293B] flex flex-wrap items-center justify-between gap-2 rounded-t-md">
    <div>
      <h2 className="text-sm font-semibold text-[#0F172A] dark:text-[#F8FAFC] tracking-tight">
        {title}
      </h2>
      {subtitle && (
        <p className="text-xs text-[#475569] dark:text-[#94A3B8] mt-0.5">{subtitle}</p>
      )}
    </div>
    {right && <div>{right}</div>}
  </div>
);

type ButtonVariant = "primary" | "secondary" | "danger" | "outline";

export const Button: React.FC<
  React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: ButtonVariant }
> = ({ variant = "primary", className = "", children, ...props }) => {
  const base =
    "inline-flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium rounded-md border transition-colors disabled:opacity-50 disabled:cursor-not-allowed";

  const variants: Record<ButtonVariant, string> = {
    primary:
      "bg-[#1E3A8A] text-white border-[#1E3A8A] hover:bg-[#172554]",
    secondary:
      "bg-[#0F172A] text-white border-[#0F172A] hover:bg-[#1E293B] dark:bg-[#334155] dark:border-[#475569]",
    danger:
      "bg-[#B91C1C] text-white border-[#B91C1C] hover:bg-[#991B1B]",
    outline:
      "bg-white dark:bg-[#111827] text-[#0F172A] dark:text-[#F8FAFC] border-[#CBD5E1] dark:border-[#334155] hover:bg-[#F8FAFC] dark:hover:bg-[#1E293B]",
  };

  return (
    <button className={`${base} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
};

export const RiskBadge: React.FC<{ risk: string }> = ({ risk }) => {
  const upper = risk.toUpperCase();
  let style =
    "bg-[#ECFDF5] text-[#065F46] border-[#6EE7B7] dark:bg-[#064E3B] dark:text-[#A7F3D0] dark:border-[#059669]";

  if (upper === "CRÍTICO" || upper === "CRITICAL") {
    style =
      "bg-[#FEF2F2] text-[#991B1B] border-[#FCA5A5] dark:bg-[#7F1D1D] dark:text-[#FECACA] dark:border-[#DC2626]";
  } else if (upper === "ALTO" || upper === "HIGH") {
    style =
      "bg-[#FEF2F2] text-[#B91C1C] border-[#FCA5A5] dark:bg-[#7F1D1D] dark:text-[#FECACA] dark:border-[#DC2626]";
  } else if (upper === "MODERADO" || upper === "MODERATE") {
    style =
      "bg-[#FFFBEB] text-[#92400E] border-[#FCD34D] dark:bg-[#78350F] dark:text-[#FDE68A] dark:border-[#D97706]";
  }

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 text-xs font-semibold border rounded ${style}`}>
      {risk}
    </span>
  );
};

export const MarkdownReportView: React.FC<{ markdown: string }> = ({ markdown }) => {
  const cleaned = sanitizeClinicalText(markdown);
  const lines = cleaned.split("\n");
  return (
    <div className="space-y-2 text-sm text-[#0F172A] dark:text-[#E2E8F0] leading-relaxed">
      {lines.map((line, idx) => {
        const trimmed = line.trim();
        if (!trimmed) return <div key={idx} className="h-1" />;
        if (/^\d+\.\s+/.test(trimmed)) {
          return (
            <h3
              key={idx}
              className="text-sm font-bold text-[#1E3A8A] dark:text-[#93C5FD] border-b border-[#E2E8F0] dark:border-[#334155] pb-1 pt-2"
            >
              {trimmed}
            </h3>
          );
        }
        if (trimmed.startsWith("- ")) {
          return (
            <div key={idx} className="flex gap-2 pl-2">
              <span className="text-[#1E3A8A] dark:text-[#93C5FD] font-bold">•</span>
              <span>{trimmed.slice(2)}</span>
            </div>
          );
        }
        return <p key={idx}>{trimmed}</p>;
      })}
    </div>
  );
};

