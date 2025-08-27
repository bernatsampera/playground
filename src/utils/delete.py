#!/bin/bash

files_to_delete=[
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00004-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00004-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00004-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00003-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00003-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00003-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00001-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00001-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00001-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00002-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00002-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00002-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00005-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00005-of-00005.safetensors",
 " /Users/bsampera/.cache/huggingface/hub/models--mlx-community--gemma-3-12b-it-bf16/snapshots/b8b9b412cb795bd6115fdce8c9a0ef0d1664db3a/model-00005-of-00005.safetensors",
 " /Users/bsampera/Library/Application Support/tts/tts_models--multilingual--multi-dataset--xtts_v2/model.pth",
 " /Users/bsampera/.cache/huggingface/hub/models--Systran--faster-whisper-medium/snapshots/08e178d48790749d25932bbc082711ddcfdfbc4f/model.bin",
 " /Users/bsampera/.cache/huggingface/hub/models--Systran--faster-whisper-medium/snapshots/08e178d48790749d25932bbc082711ddcfdfbc4f/model.bin",
 " /Users/bsampera/.cache/huggingface/hub/models--Systran--faster-whisper-medium/snapshots/08e178d48790749d25932bbc082711ddcfdfbc4f/model.bin",
 " /Users/bsampera/.cache/huggingface/hub/models--naver-clova-ix--donut-base/snapshots/a8138504038547801557466623fbc4946bb9bb68/pytorch_model.bin",
 " /Users/bsampera/.cache/huggingface/hub/models--runwayml--stable-diffusion-v1-5/snapshots/451f4fe16113bff5a5d2269ed5ad43b0592e9a14/safety_checker/model.safetensors",
]
import os
from pathlib import Path

def delete_files(file_list):
    total_deleted = 0
    total_freed = 0  # in bytes
    failed_deletions = []
    
    for filepath in file_list:

        try:
            path = Path(filepath)
            print(path)
            if path.exists():
                file_size = path.stat().st_size
                path.unlink()  # Delete the file
                total_deleted += 1
                total_freed += file_size
                print(f"✅ Deleted: {filepath} ({file_size/1024/1024:.2f} MB)")
            else:
                print(f"⚠️  File not found: {filepath}")
        except Exception as e:
            failed_deletions.append((filepath, str(e)))
            print(f"❌ Failed to delete {filepath}: {e}")
    
    return total_deleted, total_freed, failed_deletions


delete_files(files_to_delete)