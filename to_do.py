from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets 
import os

from sqlalchemy import create_engine, Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, Session

DATABASE_URL = "sqlite:///.to_do.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(
    title="API de Gerenciamento de Tarefas",
    description="API RESTful para gerenciar tarefas.",
    version="1.0.4",
    contact={
        "name": "Guilherme Magain Brum",
        "email": "guimbrum@gmail.com"
    }

)

MEU_USUARIO = "admin"
MINHA_SENHA = "12345678"

security = HTTPBasic()

class tarefaDB(Base):
    __tablename__ = "tarefas"
    id = Column(Integer, primary_key=True, index=True)
    nome_tarefa = Column(String, index=True)
    descricao_tarefa = Column(String, index=True)
    concluida = Column(Boolean, default=False)

class Tarefa(BaseModel):
    nome_tarefa: str
    descricao_tarefa: str
    concluida: bool = False

Base.metadata.create_all(bind=engine)

def sessao_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

def autenticar_usuario(credentials : HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, MEU_USUARIO)
    is_password_correct = secrets.compare_digest(credentials.password, MINHA_SENHA)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha incorretos.",
            headers={"WWW-Authenticate": "Basic"}
        )

@app.get("/tarefas")
def listar_tarefas(page: int=1, size: int=10, ordenar_por: str=None, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    if page < 1 or size <1:
        raise HTTPException(status_code=400, detail="page ou size estão com valores inválidos. Devemser maiores que 0.")

    tarefas = db.query(tarefaDB).offset((page-1) * size).limit(size).all()

    tarefas_ordenadas = sorted(tarefas, key=lambda x: getattr(x, ordenar_por) if ordenar_por else x.id)

    total_tarefas = db.query(tarefaDB).count()
    return {
        "page": page,
        "size": size,
        "total": total_tarefas,
        "banco_tarefas": tarefas_ordenadas
    }

@app.post("/adiciona_tarefa")
def adicionar_tarefa(tarefa: Tarefa, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    titulo = tarefa.nome_tarefa
    descricao = tarefa.descricao_tarefa
    concluida = tarefa.concluida

    db_tarefa = tarefaDB(
        nome_tarefa=titulo,
        descricao_tarefa=descricao,
        concluida=concluida
    )
    db.add(db_tarefa)
    db.commit()
    db.refresh(db_tarefa)
    return {"message": "Tarefa adicionada com sucesso.", "tarefa": db_tarefa }

@app.put("/atualiza_tarefa/{titulo_tarefa}")
def atualizar_tarefa(titulo_tarefa: str, tarefa: Tarefa, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    db_tarefa = db.query(tarefaDB).filter(tarefaDB.nome_tarefa == titulo_tarefa).first()
    if not db_tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

    db_tarefa.nome_tarefa = tarefa.nome_tarefa
    db_tarefa.descricao_tarefa = tarefa.descricao_tarefa
    db_tarefa.concluida = tarefa.concluida
    db.commit()
    db.refresh(db_tarefa)
    return {"message": "Tarefa atualizada com sucesso.", "tarefa": db_tarefa}

@app.delete("/deletar_tarefa/{titulo_tarefa}")
def deletar_tarefa(titulo_tarefa: str, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    db_tarefa = db.query(tarefaDB).filter(tarefaDB.nome_tarefa == titulo_tarefa).first()
    if not db_tarefa:
        raise HTTPException(status_code=404, detail="Tarefa não encontrada.")
    db.delete(db_tarefa)
    db.commit()
    return {"message": "Tarefa deletada com sucesso."}