import base64
import io

import modal

# 1. Define the Docker image with necessary dependencies
# We assume standard vllm supports DeepSeek-OCR in the latest version
image = modal.Image.debian_slim().pip_install(
    "vllm>=0.6.3", "pillow", "numpy", "transformers"
)

app = modal.App("deepseek-ocr-server")


# 2. Create a Class to hold the model in memory
@app.cls(
    gpu="A10G",  # Select a powerful GPU (A10G or A100 recommended)
    image=image,
    container_idle_timeout=300,  # Keep container alive for 5 mins after use
    timeout=600,  # Allow long generations
)
class OCRModel:
    @modal.enter()
    def load_model(self):
        """
        This runs once when the container starts.
        It loads the heavy model into GPU memory.
        """
        from vllm import LLM
        from vllm.model_executor.models.deepseek_ocr import NGramPerReqLogitsProcessor

        print("Loading DeepSeek-OCR model...")
        self.llm = LLM(
            model="deepseek-ai/DeepSeek-OCR",
            enable_prefix_caching=False,
            mm_processor_cache_gb=0,
            logits_processors=[NGramPerReqLogitsProcessor],
            trust_remote_code=True,  # Usually safe to add for newer models
        )
        print("Model loaded successfully.")

    @modal.web_endpoint(method="POST")
    async def generate(self, data: dict):
        """
        This is the HTTP endpoint.
        Input format: {"image": "base64_encoded_string...", "prompt": "optional_prompt"}
        """
        from PIL import Image
        from vllm import SamplingParams

        # 1. Parse inputs
        prompt_text = data.get("prompt", "<image>\nFree OCR.")
        image_b64 = data.get("image")

        if not image_b64:
            return {"error": "No image data provided"}

        # 2. Convert Base64 string back to PIL Image
        try:
            image_bytes = base64.b64decode(image_b64)
            image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception as e:
            return {"error": f"Invalid image data: {str(e)}"}

        # 3. Prepare input for vLLM
        # Note: vLLM LLM class is designed for batching. We create a batch of 1 here.
        model_input = [{"prompt": prompt_text, "multi_modal_data": {"image": image}}]

        # 4. Define Sampling Params (from your original code)
        sampling_param = SamplingParams(
            temperature=0.0,
            max_tokens=8192,
            extra_args=dict(
                ngram_size=30,
                window_size=90,
                whitelist_token_ids={128821, 128822},  # whitelist: <td>, </td>
            ),
            skip_special_tokens=False,
        )

        # 5. Run Generation
        # Since vLLM's LLM.generate is blocking, we run it directly.
        # In a high-throughput production setting, you might use AsyncLLMEngine,
        # but for this logic, this works fine within Modal.
        model_outputs = self.llm.generate(model_input, sampling_param)

        # 6. Extract and return text
        generated_text = model_outputs[0].outputs[0].text
        return {"text": generated_text}
