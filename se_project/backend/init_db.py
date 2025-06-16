from .db import Base, engine
from .models import User

# 테이블 생성
Base.metadata.create_all(bind=engine)
