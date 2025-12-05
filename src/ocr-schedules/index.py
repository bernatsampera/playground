import base64
import io
import os

import modal

# Define constants
MODEL_NAME = "deepseek-ai/DeepSeek-OCR"  # HuggingFace model to download
MODEL_DIR = "/model"  # Local directory inside the image


def download_model_to_image():
    # Downloads the model weights into the container image at build time
    from huggingface_hub import snapshot_download

    os.makedirs(MODEL_DIR, exist_ok=True)
    print(f"Downloading {MODEL_NAME} to {MODEL_DIR}...")
    snapshot_download(
        MODEL_NAME,
        local_dir=MODEL_DIR,
        ignore_patterns=["*.h5"],  # Skip unused large files
    )
    print("Download complete.")


# Build a Modal image with dependencies and the model pre-downloaded
image = (
    modal.Image.debian_slim()
    .pip_install("vllm>=0.6.3", "pillow", "numpy", "transformers", "huggingface_hub")
    .run_function(download_model_to_image)
)

app = modal.App("deepseek-ocr-server")


@app.cls(
    gpu="A10G",  # GPU type for running the OCR model
    image=image,  # Use the custom-built image above
    scaledown_window=60,  # Auto-scale down after 2 minutes idle
    timeout=120,  # Max runtime allowed per container
)
class OCRModel:
    @modal.enter()
    def load_model(self):
        # Runs when the container starts; loads the OCR model into GPU memory
        from vllm import LLM
        from vllm.model_executor.models.deepseek_ocr import NGramPerReqLogitsProcessor

        print("Loading model...")

        self.llm = LLM(
            model=MODEL_DIR,  # Load from local directory
            enable_prefix_caching=False,
            mm_processor_cache_gb=0,
            logits_processors=[NGramPerReqLogitsProcessor],
            enforce_eager=True,  # Faster startup (disable torch.compile & CUDA graph)
        )
        print("Model loaded successfully.")

    @modal.fastapi_endpoint(method="POST")
    async def generate(self, data: dict):
        # API endpoint that accepts an image + optional prompt and returns OCR text
        from PIL import Image
        from vllm import SamplingParams

        prompt_text = data.get("prompt", "<image>\nFree OCR.")
        image_b64 = data.get("image")

        if not image_b64:
            return {"error": "No image data provided"}

        # Decode and load the input image
        try:
            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return {"error": f"Invalid image data: {str(e)}"}

        # vLLM expects a list of request objects
        model_input = [{"prompt": prompt_text, "multi_modal_data": {"image": image}}]

        # Configure decoding — deterministic, large token limit, OCR-specific settings
        sampling_param = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            extra_args=dict(
                ngram_size=30,
                window_size=90,
                whitelist_token_ids={128821, 128822},
            ),
            skip_special_tokens=False,
        )

        # Run inference (blocking call but fine for single requests)
        model_outputs = self.llm.generate(model_input, sampling_param)
        generated_text = model_outputs[0].outputs[0].text

        return {"text": generated_text}
