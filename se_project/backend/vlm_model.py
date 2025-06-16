def recognize(image_path: str) -> list[str]:
    """
    이미지 경로를 받아서 재료 목록을 추출하는 더미 함수입니다.
    실제로는 VLM 모델을 여기에 연결해야 합니다.
    """
    print(f"이미지 인식: {image_path}")
    # 테스트용으로 고정된 재료 목록 반환
    return ["계란", "우유", "소금"]

