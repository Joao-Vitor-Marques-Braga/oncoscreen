"""Integration tests for FastAPI endpoints with mocked Vision & SLM engines."""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.domain.entities.anamnesis import Anamnesis
from app.domain.entities.clinical_report import ClinicalReport, GuardrailAssessment
from app.domain.interfaces.slm_engine import SLMEngine
from app.domain.interfaces.vision_engine import VisionAnalysisResult, VisionEngine
from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant
from app.infrastructure.config import Settings
from main import create_app


class MockVisionEngine(VisionEngine):
    async def analyze(self, image_bytes: bytes) -> VisionAnalysisResult:
        buf = io.BytesIO()
        Image.new("RGB", (64, 64), color=(180, 50, 50)).save(buf, format="JPEG")
        jpeg_bytes = buf.getvalue()
        return VisionAnalysisResult(
            probability=0.30,
            anatomical_quadrant=AnatomicalQuadrant.LOWER_LEFT,
            original_jpeg_bytes=jpeg_bytes,
            heatmap_png_bytes=jpeg_bytes,
            overlay_jpeg_bytes=jpeg_bytes,
            inference_time_ms=12.5,
        )

    def status(self) -> dict[str, object]:
        return {"engine": "MockVision", "device": "cpu", "weights_loaded": True}


class MockSLMEngine(SLMEngine):
    async def generate_clinical_report(
        self,
        patient_name: str,
        cnn_probability: float,
        threshold: float,
        quadrant: AnatomicalQuadrant,
        anamnesis: Anamnesis,
        guardrail: GuardrailAssessment,
    ) -> ClinicalReport:
        return ClinicalReport(
            markdown_body=f"## 1. Síntese Diagnóstica\nLaudo mock para {patient_name} ({guardrail.final_risk.value}).",
            model_used="mock-qwen2.5:3b",
            generated_via_fallback=False,
        )

    async def health_check(self) -> dict[str, object]:
        return {"online": True, "configured_model": "mock-qwen2.5:3b"}


@pytest.fixture()
def client(tmp_path: Path):
    db_path = tmp_path / "test.db"
    storage_dir = tmp_path / "storage"
    cfg = Settings(
        database_url=f"sqlite+aiosqlite:///{db_path.as_posix()}",
        storage_dir=str(storage_dir),
        weights_path=str(tmp_path / "nonexistent.pth"),
    )
    app = create_app(cfg)
    with TestClient(app) as test_client:
        app.state.container.vision_engine = MockVisionEngine()
        app.state.container.slm_engine = MockSLMEngine()
        yield test_client


def test_end_to_end_doctor_triage_and_patient_rbac(client: TestClient) -> None:
    # 1. Doctor login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"identifier": "doutor@oncoscreen.ai", "password": "admin123"},
    )
    assert login_resp.status_code == 200
    doctor_token = login_resp.json()["access_token"]
    doc_headers = {"Authorization": f"Bearer {doctor_token}"}

    # 2. Register patient by CPF
    patient_resp = client.post(
        "/api/v1/patients/lookup-or-register",
        headers=doc_headers,
        json={
            "cpf": "52998224725",
            "full_name": "João da Silva",
            "birth_date": "1975-08-20",
            "phone_whatsapp": "11988887777",
        },
    )
    assert patient_resp.status_code == 200
    patient_id = patient_resp.json()["id"]
    assert patient_resp.json()["newly_created"] is True

    # 3. Execute multimodal triage (triggering false-negative guardrail)
    img_buf = io.BytesIO()
    Image.new("RGB", (100, 100), color=(200, 80, 80)).save(img_buf, format="JPEG")
    img_buf.seek(0)

    anamnesis_payload = {
        "active_smoking": True,
        "evolution_gt_14_days": True,
        "erythroplakia": True,
        "clinical_notes": "Lesão em borda lateral da língua.",
    }
    triage_resp = client.post(
        "/api/v1/triage/execute",
        headers=doc_headers,
        data={
            "patient_id": patient_id,
            "threshold": "0.50",
            "anamnesis_json": json.dumps(anamnesis_payload),
        },
        files={"image": ("lesion.jpg", img_buf, "image/jpeg")},
    )
    assert triage_resp.status_code == 200
    triage_data = triage_resp.json()
    exam_id = triage_data["exam_id"]
    assert triage_data["guardrail"]["final_risk"] == "ALTO"
    assert triage_data["guardrail"]["guardrail_triggered"] is True

    # 4. Patient login with CPF + birth date DDMMYYYY
    pat_login = client.post(
        "/api/v1/auth/login",
        json={"identifier": "529.982.247-25", "password": "20081975"},
    )
    assert pat_login.status_code == 200
    pat_headers = {"Authorization": f"Bearer {pat_login.json()['access_token']}"}

    # 5. Patient RBAC: forbidden on doctor-only routes
    forbidden_resp = client.post(
        "/api/v1/patients/lookup-or-register",
        headers=pat_headers,
        json={"cpf": "52998224725"},
    )
    assert forbidden_resp.status_code == 403

    # 6. Patient can read own exams and exam detail (PDF is generated on frontend)
    exams_resp = client.get("/api/v1/exams", headers=pat_headers)
    assert exams_resp.status_code == 200
    assert len(exams_resp.json()) == 1

    detail_resp = client.get(f"/api/v1/exams/{exam_id}", headers=pat_headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["patient_birth_date"] == "1975-08-20"
    assert detail_data["doctor_name"] != ""

    # Confirm backend PDF endpoint no longer exists
    pdf_resp = client.get(f"/api/v1/exams/{exam_id}/pdf", headers=pat_headers)
    assert pdf_resp.status_code == 404


def test_sanitize_report_text_strips_markdown_fences_and_hashes() -> None:
    from app.infrastructure.llm.ollama_slm_client import sanitize_report_text

    dirty = (
        "```markdown\n\n"
        "### 1. Síntese Clínica\n\n"
        "Texto **em negrito** com `codigo`.\n"
        "•\nItem quebrado\n"
        "```"
    )
    cleaned = sanitize_report_text(dirty)
    assert "```" not in cleaned
    assert "markdown" not in cleaned
    assert "###" not in cleaned
    assert "**" not in cleaned
    assert "`" not in cleaned
    assert "1. Síntese Clínica" in cleaned
    assert "- Item quebrado" in cleaned


def test_sanitize_report_text_replaces_surgery_with_biopsy() -> None:
    from app.infrastructure.llm.ollama_slm_client import sanitize_report_text

    raw = (
        "4. Conduta Recomendada\n"
        "Recomenda-se encaminhamento para Cirurgia de Cabeça e Pescoço para avaliação cirúrgica emergencial."
    )
    cleaned = sanitize_report_text(raw)
    assert "cirurg" not in cleaned.lower()
    assert "biópsia" in cleaned.lower()
    assert "Estomatologia" in cleaned

