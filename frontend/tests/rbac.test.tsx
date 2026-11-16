import { describe, expect, it, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import App from "@/App";

// Mock axios client to avoid network calls during unit tests
vi.mock("@/shared/api/client", () => ({
  apiClient: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn(),
    put: vi.fn(),
  },
}));

describe("RBAC Conditional Rendering (Doctor vs Patient)", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("renders Doctor navigation tabs and triage workspace for DOCTOR role", () => {
    localStorage.setItem(
      "oncoscreen_auth",
      JSON.stringify({
        user_id: "doc-1",
        full_name: "Dr. Carlos",
        role: "DOCTOR",
        access_token: "fake-token",
      })
    );

    render(<App />);
    expect(screen.getByText("Triagem Multimodal")).toBeInTheDocument();
    expect(screen.getByText("Histórico de Exames")).toBeInTheDocument();
    expect(screen.getByText("Métricas Clínicas")).toBeInTheDocument();
    expect(screen.getByText("Configurações & Modelos")).toBeInTheDocument();
    expect(screen.getByText("1. Identificação do Paciente por CPF")).toBeInTheDocument();
  });

  it("renders strictly read-only Patient view and hides Doctor tabs for PATIENT role", () => {
    localStorage.setItem(
      "oncoscreen_auth",
      JSON.stringify({
        user_id: "pat-1",
        full_name: "Maria Silva",
        role: "PATIENT",
        patient_id: "p-123",
        access_token: "fake-token",
      })
    );

    render(<App />);
    expect(screen.getByText("Meus Exames")).toBeInTheDocument();
    expect(screen.queryByText("Triagem Multimodal")).not.toBeInTheDocument();
    expect(screen.queryByText("Métricas Clínicas")).not.toBeInTheDocument();
    expect(screen.queryByText("Configurações & Modelos")).not.toBeInTheDocument();
  });
});

