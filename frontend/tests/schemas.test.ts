import { describe, expect, it } from "vitest";
import { anamnesisSchema } from "@/features/triage/anamnesisSchema";
import { patientLookupSchema } from "@/features/patients/PatientLookupCard";
import { sanitizeClinicalText } from "@/shared/utils/generateClinicalPdf";

describe("Zod Clinical Schemas", () => {
  it("validates structured anamnesis defaults and flags", () => {
    const parsed = anamnesisSchema.parse({
      active_smoking: true,
      evolution_gt_14_days: true,
      clinical_notes: "Lesão em assoalho bucal.",
    });
    expect(parsed.active_smoking).toBe(true);
    expect(parsed.evolution_gt_14_days).toBe(true);
    expect(parsed.erythroplakia).toBe(false);
    expect(parsed.clinical_notes).toBe("Lesão em assoalho bucal.");
  });

  it("rejects clinical_notes exceeding 1000 characters", () => {
    const res = anamnesisSchema.safeParse({
      clinical_notes: "a".repeat(1001),
    });
    expect(res.success).toBe(false);
  });

  it("normalizes formatted CPF and rejects short CPF", () => {
    const ok = patientLookupSchema.safeParse({ cpf: "529.982.247-25" });
    expect(ok.success).toBe(true);
    if (ok.success) {
      expect(ok.data.cpf).toBe("52998224725");
    }

    const bad = patientLookupSchema.safeParse({ cpf: "12345" });
    expect(bad.success).toBe(false);
  });

  it("strips markdown fences, hashes, and broken bullets from SLM report text", () => {
    const dirty = "```markdown\n\n### 1. Síntese Clínica\n\n•\nItem 1\n**Negrito**\n```";
    const clean = sanitizeClinicalText(dirty);
    expect(clean).not.toContain("```");
    expect(clean).not.toContain("markdown");
    expect(clean).not.toContain("###");
    expect(clean).not.toContain("**");
    expect(clean).toContain("1. Síntese Clínica");
    expect(clean).toContain("- Item 1");
  });
});

