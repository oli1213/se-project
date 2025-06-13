#!/usr/bin/env python3
import os
import sys
import argparse
import logging
from ollama import chat, OllamaError

def setup_logger():
    logger = logging.getLogger("IngredientRecognizer")
    logger.setLevel(logging.INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
    logger.addHandler(ch)
    return logger

def parse_args():
    p = argparse.ArgumentParser(
        description="Ollama VLM으로 이미지 속 식재료를 인식합니다."
    )
    p.add_argument(
        "-m", "--model",
        default="llama3.2-vision",
        help="사용할 Ollama 모델 이름 (예: llama3.2-vision, gemma3:4b)"
    )
    p.add_argument(
        "-i", "--image",
        default="images/fridge.jpg",
        help="분석할 이미지 경로"
    )
    p.add_argument(
        "-q", "--question",
        default="이 이미지에 있는 식재료를 알려줘.",
        help="모델에 보낼 질문(프롬프트)"
    )
    return p.parse_args()

def recognize_ingredients(model_name: str, image_path: str, question: str, logger):
    if not os.path.isfile(image_path):
        logger.error(f"이미지 파일을 찾을 수 없습니다: {image_path}")
        sys.exit(1)
    msg = {
        "role": "user",
        "content": question,
        "images": [image_path],
    }
    try:
        logger.info(f"모델 '{model_name}' 호출 중...")
        resp = chat(model=model_name, messages=[msg])
    except OllamaError as e:
        logger.error(f"Ollama 호출 오류: {e}")
        sys.exit(1)

    content = resp.get("message", {}).get("content", "")
    if not content:
        logger.warning("모델이 응답을 반환하지 않았습니다.")
    else:
        logger.info("인식된 식재료:")
        for item in content.split(","):
            logger.info(f" - {item.strip()}")

def main():
    logger = setup_logger()
    args = parse_args()
    recognize_ingredients(
        model_name=args.model,
        image_path=args.image,
        question=args.question,
        logger=logger
    )

if __name__ == "__main__":
    main()
