"""CPU-Optimized Vision Engine (ConvNeXt-Tiny / EfficientNet-B0) with real Grad-CAM localization."""

from __future__ import annotations

import asyncio
import io
import logging
import time
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision import models, transforms

from app.domain.interfaces.vision_engine import VisionAnalysisResult, VisionEngine
from app.domain.value_objects.anatomical_quadrant import AnatomicalQuadrant

logger = logging.getLogger(__name__)


class EfficientNetVisionEngine(VisionEngine):
    """Auto-detecting ConvNeXt-Tiny / EfficientNet-B0 + Grad-CAM engine tuned for CPU inference."""

    def __init__(self, weights_path: str, num_threads: int = 4) -> None:
        self._device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        if self._device.type == "cpu":
            torch.set_num_threads(max(1, num_threads))

        self._weights_path = Path(weights_path)
        self._weights_loaded = False
        self._architecture = "EfficientNet-B0"
        self._model = self._build_and_load_model()
        self._model.eval()

        self._preprocess = transforms.Compose(
            [
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225],
                ),
            ]
        )

    def _build_and_load_model(self) -> nn.Module:
        if self._weights_path.is_file():
            try:
                checkpoint = torch.load(self._weights_path, map_location=self._device, weights_only=True)
                state_dict = (
                    checkpoint["model_state_dict"]
                    if isinstance(checkpoint, dict) and "model_state_dict" in checkpoint
                    else checkpoint
                )

                if isinstance(state_dict, dict):
                    state_dict = {
                        (k[len("backbone."):] if k.startswith("backbone.") else k): v
                        for k, v in state_dict.items()
                    }

                    # Detect ConvNeXt-Tiny vs EfficientNet-B0 from checkpoint structure
                    is_convnext = any("layer_scale" in k for k in state_dict.keys())
                    if is_convnext:
                        model = models.convnext_tiny(weights=None)
                        in_features = model.classifier[2].in_features
                        if "classifier.2.1.weight" in state_dict:
                            out_dim = int(state_dict["classifier.2.1.weight"].shape[0])
                            model.classifier[2] = nn.Sequential(
                                nn.Dropout(p=0.4),
                                nn.Linear(in_features, out_dim),
                            )
                        else:
                            head_w = state_dict.get("classifier.2.weight")
                            out_dim = int(head_w.shape[0]) if head_w is not None else 1
                            model.classifier[2] = nn.Linear(in_features, out_dim)
                        self._architecture = "ConvNeXt-Tiny"
                    else:
                        model = models.efficientnet_b0(weights=None)
                        in_features = model.classifier[1].in_features
                        head_w = state_dict.get("classifier.1.weight")
                        out_dim = int(head_w.shape[0]) if head_w is not None else 1
                        model.classifier[1] = nn.Linear(in_features, out_dim)
                        self._architecture = "EfficientNet-B0"

                    missing, unexpected = model.load_state_dict(state_dict, strict=False)
                    if len(missing) == 0 and len(unexpected) == 0:
                        self._weights_loaded = True
                        logger.info(
                            "Loaded %s weights cleanly from %s (0 missing, 0 unexpected)",
                            self._architecture,
                            self._weights_path,
                        )
                    else:
                        self._weights_loaded = len(missing) < 10
                        logger.warning(
                            "Loaded %s weights from %s with missing=%d, unexpected=%d",
                            self._architecture,
                            self._weights_path,
                            len(missing),
                            len(unexpected),
                        )
                    return model.to(self._device)
            except Exception as exc:
                logger.warning(
                    "Failed to load weights from %s: %s. Falling back to initialized EfficientNet-B0.",
                    self._weights_path,
                    exc,
                )

        # Fallback: uninitialized EfficientNet-B0
        model = models.efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, 1)
        self._architecture = "EfficientNet-B0"
        return model.to(self._device)

    async def analyze(self, image_bytes: bytes) -> VisionAnalysisResult:
        return await asyncio.to_thread(self._analyze_sync, image_bytes)

    def _analyze_sync(self, image_bytes: bytes) -> VisionAnalysisResult:
        start = time.perf_counter()

        pil_img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        display_img = self._resize_for_display(pil_img, max_side=640)
        disp_w, disp_h = display_img.size

        input_tensor = self._preprocess(pil_img).unsqueeze(0).to(self._device)
        input_tensor.requires_grad_(True)

        activations: Optional[torch.Tensor] = None
        gradients: Optional[torch.Tensor] = None

        def forward_hook(_module: nn.Module, _inp: tuple, output: torch.Tensor) -> None:
            nonlocal activations
            activations = output.detach()

        def backward_hook(_module: nn.Module, _grad_in: tuple, grad_out: tuple) -> None:
            nonlocal gradients
            gradients = grad_out[0].detach()

        target_layer = self._model.features[-1]
        fwd_handle = target_layer.register_forward_hook(forward_hook)
        bwd_handle = target_layer.register_full_backward_hook(backward_hook)

        try:
            self._model.zero_grad(set_to_none=True)
            logits = self._model(input_tensor)

            if logits.shape[-1] == 2:
                probs = torch.softmax(logits, dim=-1)
                prob = float(probs[0, 1].item())
                score = logits[0, 1]
            else:
                prob = float(torch.sigmoid(logits[0, 0]).item())
                score = logits[0, 0]

            score.backward()
        finally:
            fwd_handle.remove()
            bwd_handle.remove()

        cam = self._compute_gradcam(activations, gradients)
        quadrant = self._map_quadrant(cam)

        cam_resized = cv2.resize(cam, (disp_w, disp_h), interpolation=cv2.INTER_CUBIC)
        cam_uint8 = np.uint8(np.clip(cam_resized * 255.0, 0, 255))
        heatmap_bgr = cv2.applyColorMap(cam_uint8, cv2.COLORMAP_JET)

        orig_rgb = np.array(display_img)
        orig_bgr = cv2.cvtColor(orig_rgb, cv2.COLOR_RGB2BGR)
        overlay_bgr = cv2.addWeighted(orig_bgr, 0.55, heatmap_bgr, 0.45, 0)

        original_jpeg_bytes = self._encode_bgr(orig_bgr, ".jpg", quality=85)
        heatmap_png_bytes = self._encode_bgr(heatmap_bgr, ".png")
        overlay_jpeg_bytes = self._encode_bgr(overlay_bgr, ".jpg", quality=85)

        elapsed_ms = (time.perf_counter() - start) * 1000.0
        return VisionAnalysisResult(
            probability=round(prob, 4),
            anatomical_quadrant=quadrant,
            original_jpeg_bytes=original_jpeg_bytes,
            heatmap_png_bytes=heatmap_png_bytes,
            overlay_jpeg_bytes=overlay_jpeg_bytes,
            inference_time_ms=round(elapsed_ms, 2),
        )

    @staticmethod
    def _compute_gradcam(
        activations: Optional[torch.Tensor],
        gradients: Optional[torch.Tensor],
    ) -> np.ndarray:
        if activations is None or gradients is None:
            return np.ones((7, 7), dtype=np.float32) * 0.5

        weights = gradients.mean(dim=(2, 3), keepdim=True)
        cam = (weights * activations).sum(dim=1, keepdim=True)
        cam = torch.relu(cam).squeeze().cpu().numpy()

        cam_min, cam_max = float(cam.min()), float(cam.max())
        if cam_max - cam_min > 1e-8:
            cam = (cam - cam_min) / (cam_max - cam_min)
        else:
            cam = np.zeros_like(cam, dtype=np.float32)
        return cam.astype(np.float32)

    @staticmethod
    def _map_quadrant(cam: np.ndarray) -> AnatomicalQuadrant:
        h, w = cam.shape
        y_idx, x_idx = np.unravel_index(np.argmax(cam), cam.shape)
        y_norm = y_idx / max(1, h - 1)
        x_norm = x_idx / max(1, w - 1)

        if 0.35 <= x_norm <= 0.65 and 0.35 <= y_norm <= 0.65:
            return AnatomicalQuadrant.CENTRAL_ANTERIOR
        if y_norm < 0.25 and 0.30 <= x_norm <= 0.70:
            return AnatomicalQuadrant.POSTERIOR_OROPHARYNX
        if y_norm < 0.5:
            return AnatomicalQuadrant.UPPER_LEFT if x_norm < 0.5 else AnatomicalQuadrant.UPPER_RIGHT
        return AnatomicalQuadrant.LOWER_LEFT if x_norm < 0.5 else AnatomicalQuadrant.LOWER_RIGHT

    @staticmethod
    def _resize_for_display(img: Image.Image, max_side: int = 640) -> Image.Image:
        w, h = img.size
        scale = min(1.0, max_side / max(w, h))
        if scale < 1.0:
            return img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
        return img

    @staticmethod
    def _encode_bgr(img_bgr: np.ndarray, ext: str, quality: int = 85) -> bytes:
        params = [cv2.IMWRITE_JPEG_QUALITY, quality] if ext == ".jpg" else []
        ok, buf = cv2.imencode(ext, img_bgr, params)
        if not ok:
            raise RuntimeError("Falha ao codificar imagem processada.")
        return buf.tobytes()

    def status(self) -> dict[str, object]:
        return {
            "engine": f"{self._architecture} (PyTorch + Grad-CAM)",
            "device": str(self._device),
            "cpu_threads": torch.get_num_threads() if self._device.type == "cpu" else None,
            "weights_path": str(self._weights_path),
            "weights_loaded": self._weights_loaded,
        }
