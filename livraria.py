from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import os
import redis
import json
from fastapi import BackgroundTasks
from tasks import somar, fatorial
from celery_app import celery_app
from celery.result import AsyncResult

from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.orm import Session

import asyncio
import logging.config
import yaml
from elasticsearch import Elasticsearch
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./.to_do.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = os.getenv("ELASTICSEARCH_INDEX", "livros-logs")
es_client = Elasticsearch([ELASTICSEARCH_URL])

REDIS_HOST = os.getenv("REDIS_HOST", "livros-redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)

es = Elasticsearch(hosts=["https://elastic:9200"])
with open("logging.yaml", "r") as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

logger = logging.getLogger(__name__)
logger.info("API inicializada com sucesso!")

app = FastAPI(
    title="API de Gerenciamento de Biblioteca",
    description="API RESTful para gerenciar livros e empréstimos.",
    version="1.0.0",
    contact={
        "name": "Guilherme Magain Brum",
        "email": "guimbrum@gmail.com"
    }
)

MEU_USUARIO = os.getenv("MEU_USUARIO", "guimbrum")
MINHA_SENHA = os.getenv("MINHA_SENHA", "1234Gui")

security = HTTPBasic()

class LivroDB(Base):
    __tablename__ = "livros"
    id = Column(Integer, primary_key=True, index=True)
    nome_livro = Column(String, index=True)
    autor_livro = Column(String, index=True)
    ano_livro = Column(Integer)

class Livro(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int

Base.metadata.create_all(bind=engine)

def salvar_livro_redis(livro_id: int, livro: Livro):
    redis_client.set(f"livro:{livro_id}", json.dumps(livro.model_dump()))

def deletar_livro_redis(livro_id: int):
    redis_client.delete(f"livro:{livro_id}")

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
            detail="Usuário ou senha inválidos.",
            headers={"WWW-Authenticate": "Basic"},
        )

@app.get("/")
def hello_world():
    return {"Hello": "world!"}

@app.post("/calcular/soma")
def calcular_soma(a: int, b: int):
    tarefa = somar.delay(a, b)
    redis_client.lpush("tarefas_ids", tarefa.id)
    redis_client.ltrim("tarefas_ids", 0, 49)

    return {
        "task_id": tarefa.id,
        "message": "Tarefa de soma enviada para execução"
    }

@app.post("/calcular/fatorial")
def calcular_fatorial(n: int):
    tarefa = fatorial.delay(n)
    redis_client.lpush("tarefas_ids", tarefa.id)
    redis_client.ltrim("tarefas_ids", 0, 49)

    return {
        "task_id": tarefa.id,
        "message": "Tarefa de fatorial enviada para execução"
    }

@app.get("/tarefas/recentes")
def listar_tarefas_recentes():
    ids = redis_client.lrange("tarefas_ids", 0, -1)
    tarefas = []

    for task_id in ids:
        resultado = AsyncResult(task_id, app=celery_app)
        tarefas.append({
            "task_id": task_id,
            "status": resultado.status,
            "resultado": resultado.result if resultado.successful() else None
        })
    return tarefas

@app.get("/debug/redis")
def ver_livros_redis():
    chaves = redis_client.keys("livro:*")
    livros = []

    for chave in chaves:
        valor = redis_client.get(chave)
        ttl = redis_client.ttl(chave)
        livros.append({"chave": chave, "valor": json.loads(valor), "ttl": ttl})
    return livros

@app.get("/livros")
async def get_livro(page: int = 1, limit: int = 10, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if page < 1 or limit < 1:
        raise HTTPException(status_code=400, detail="Page ou limit estão com valores inválidos. Devem ser maiores que 0.")

    cache_key = f"livros:page={page}&limit={limit}"
    cached = redis_client.get(cache_key)

    if cached:
        return json.loads(cached)

    livros = db.query(LivroDB).offset((page - 1) * limit).limit(limit).all()

    if not livros:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado.")

    total_livros = db.query(LivroDB).count()

    resposta = {
        "page": page,
        "limit": limit,
        "total": total_livros,
        "livros": [
            {
                "id": livro.id,
                "nome_livro": livro.nome_livro,
                "autor_livro": livro.autor_livro,
                "ano_livro": livro.ano_livro
            } for livro in livros
        ]
    }

    redis_client.setex(cache_key, 30, json.dumps(resposta))
    return resposta

@app.post("/adiciona")
async def post_livro(livro: Livro, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.nome_livro == livro.nome_livro, LivroDB.autor_livro == livro.autor_livro).first()
    if db_livro:
        raise HTTPException(status_code=400, detail="Esse livro já existe dentro do banco de dados!")

    novo_livro = LivroDB(nome_livro=livro.nome_livro, autor_livro=livro.autor_livro, ano_livro=livro.ano_livro)
    db.add(novo_livro)
    db.commit()
    db.refresh(novo_livro)

    salvar_livro_redis(novo_livro.id, livro)

    return {"message": "Livro adicionado com sucesso!", "livro": {"id": novo_livro.id, "nome_livro": novo_livro.nome_livro, "autor_livro": novo_livro.autor_livro, "ano_livro": novo_livro.ano_livro}}

@app.put("/atualiza/{id_livro}")
async def put_livro(id_livro: int, livro: Livro, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")

    db_livro.nome_livro = livro.nome_livro
    db_livro.autor_livro = livro.autor_livro
    db_livro.ano_livro = livro.ano_livro

    db.commit()
    db.refresh(db_livro)

    return {"message": "Livro atualizado com sucesso!", "livro": {"id": db_livro.id, "nome_livro": db_livro.nome_livro, "autor_livro": db_livro.autor_livro, "ano_livro": db_livro.ano_livro}}

@app.delete("/deletar/{id_livro}")
async def delete_livro(id_livro: int, db: Session = Depends(sessao_db), credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    db_livro = db.query(LivroDB).filter(LivroDB.id == id_livro).first()
    if not db_livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")

    db.delete(db_livro)
    db.commit()

    deletar_livro_redis(id_livro)

    return {"message": "Livro deletado com sucesso!", "livro": {"id": db_livro.id, "nome_livro": db_livro.nome_livro, "autor_livro": db_livro.autor_livro, "ano_livro": db_livro.ano_livro}}
