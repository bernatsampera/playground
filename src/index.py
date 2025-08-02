import os
import heapq

# Directories to scan (you can add more if needed)
DEFAULT_DIRS = [
    os.path.expanduser("~/.cache/huggingface"),
    os.path.expanduser("~/.cache/torch"),
    os.path.expanduser("~/.torch"),
    os.path.expanduser("~/.keras"),
    os.path.expanduser("~/.ollama/models"),
    os.path.expanduser("~/.cache/huggingface/hub/"),
    os.path.expanduser("~")  # fallback: home directory
]

# Extensions that typically indicate model weights
MODEL_EXTENSIONS = {".bin", ".pt", ".pth", ".safetensors", ".gguf", ".ckpt"}

def find_largest_model_files(dirs=DEFAULT_DIRS, top_n=20, min_size_mb=100):
    largest_files = []
    min_size_bytes = min_size_mb * 1024 * 1024

    for directory in dirs:
        if not os.path.exists(directory):
            continue

        print(f"🔍 Scanning: {directory}")
        for root, _, files in os.walk(directory):
            for file in files:
                if not any(file.endswith(ext) for ext in MODEL_EXTENSIONS):
                    continue

                try:
                    file_path = os.path.join(root, file)
                    size = os.path.getsize(file_path)
                    if size >= min_size_bytes:
                        heapq.heappush(largest_files, (size, file_path))
                        if len(largest_files) > top_n:
                            heapq.heappop(largest_files)
                except (OSError, PermissionError):
                    pass

    # Sort by size (largest first)
    largest_files = sorted(largest_files, key=lambda x: x[0], reverse=True)
    print("\n📦 Largest Model Files:")
    for size, path in largest_files:
        print(f"{size / (1024*1024):8.2f} MB  -  {path}")

if __name__ == "__main__":
    find_largest_model_files()