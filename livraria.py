# Documentação Swagger -> Documentar os endppoints da aplicação (API) 

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from fastapi.security import  HTTPBasic, HTTPBasicCredentials 
import secrets
import os

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session

DATABASE_URL = "sqlite:///.livraria.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Inicializa a API
app = FastAPI(
    title="API de Gerenciamento de Biblioteca",
    description="API RESTful para gerenciar livros e empréstimos.",
    version="1.0.0",
    contact={
        "name": "Guilherme Magain Brum",
        "email": "guimbrum@gmail.com",
    },
)

MEU_USUARIO = "admin"
MINHA_SENHA = "794613825Gui@"

security = HTTPBasic()

meus_livros = {}

class LivroDB(Base): #tabela de banco de dados para armazenar os livros, substituindo a estrutura de dados em memória (dicionário)
    __tablename__ = "livros"
    id = Column(Integer, primary_key=True, index=True)
    nome_livro = Column(String, index=True)
    autor_livro = Column(String, index=True)
    ano_livro = Column(Integer)

class Livro(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int

Base.metadata.create_all(bind=engine) #cria as tabelas no banco de dados, caso não existam

def sessao_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def autenticar_meu_usuario(credentials: HTTPBasicCredentials = Depends(security)):
    is_username_correct = secrets.compare_digest(credentials.username, MEU_USUARIO)
    is_password_correct = secrets.compare_digest(credentials.password, MINHA_SENHA)

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha invalidos.",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/livros")
def get_livro(page: int = 1, limit: int = 10, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if page < 1 or limit <1:
        raise HTTPException(status_code=400, detail="Page ou limit estão com valores inválidos. Devem ser maiores que 0.")

    livros = db.query(LivroDB).offset((page-1) * limit).limit(limit).all()

    if not livros:
        return {"message": "Nenhum livro encontrado."}

    total_livros = db.query(LivroDB).count()

    return {
        "page": page,
        "limit": limit,
        "total": total_livros,
        "meus_livros": [{"id": livro.id, "nome_livro": livro.nome_livro, "autor_livro": livro.autor_livro, "ano_livro": livro.ano_livro} for livro in livros]
    }

@app.post("/adiciona")
def post_livro(livro: Livro, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.nome_livro == livro.nome_livro, LivroDB.autor_livro == livro.autor_livro).first()
    if db_livro:
        raise HTTPException(status_code=400, detail="Esse livro já existe dentro do banco de dados!")

    novo_livro = LivroDB(nome_livro=livro.nome_livro, autor_livro=livro.autor_livro, ano_livro=livro.ano_livro)
    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)

    return {"message": "Livro adicionado com sucesso!", "livro": {"id": novo_livro.id, "nome_livro": novo_livro.nome_livro, "autor_livro": novo_livro.autor_livro, "ano_livro": novo_livro.ano_livro}} 

@app.put("/atualiza/{id_livro}")
def put_livro(id_livro: int, livro: Livro, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first() #conexão com o banco de dados e busca o livro pelo id
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")

    db_livro.nome_livro = livro.nome_livro
    db_livro.autor_livro = livro.autor_livro
    db_livro.ano_livro = livro.ano_livro

    db.commit()
    db.refresh(db_livro)

    return {"message": "Livro atualizado com sucesso!", "livro": {"id": db_livro.id, "nome_livro": db_livro.nome_livro, "autor_livro": db_livro.autor_livro, "ano_livro": db_livro.ano_livro}}
  

@app.delete("/deletar/{id_livro}")
def delete_livro(id_livro: int, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    
    db.delete(db_livro)
    db.commit()
    
    return {"message": "Livro deletado com sucesso!", "livro": {"id": db_livro.id, "nome_livro": db_livro.nome_livro, "autor_livro": db_livro.autor_livro, "ano_livro": db_livro.ano_livro}}