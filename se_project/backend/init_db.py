import db
import models

# 테이블 생성
db.Base.metadata.create_all(bind=db.engine)

print("Database tables created successfully!")
