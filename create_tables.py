from app.core.database import engine
from app.models.base import Base
from app.models.user import User
from app.models.lead import Lead

Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso.")
print(Base.metadata.tables.keys())