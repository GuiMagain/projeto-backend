# Documentação Swagger -> Documentar os endppoints da aplicação (API) 

from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, List, Optional
from fastapi.security import  HTTPBasic, HTTPBasicCredentials 
import secrets
import os

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

# ---------------------------------------------------------
# Banco de Dados em Memória (Variáveis)
# ---------------------------------------------------------
livros: Dict[str, dict] = {}
historico_emprestimos: List[dict] = []

# ---------------------------------------------------------
# Modelos de Dados (Estruturas de Entrada)
# ---------------------------------------------------------

meus_livros = {}

class Livro(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int

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
def get_livro(page: int=1, limit: int=10, credentials: HTTPBasicCredentials = Depends(autenticar_meu_usuario)):
    if page < 1 or limit <1:
        raise HTTPException(status_code=400, detail="Page ou limit estão com valores inválidos. Devem ser maiores que 0.")

    if not meus_livros:
        return {"message": "Nenhum livro encontrado."}

    start = (page - 1) * limit
    end = start + limit

    livros_paginados = [
        {"id": id_livro, "nome_livro": livro_data["nome_livro"], "autor_livro": livro_data["autor_livro"], "ano_livro": livro_data["ano_livro"]}
        for id_livro, livro_data in list(meus_livros.items())[start:end]
    ]
    return {
        "page": page,
        "limit": limit,
        "total": len(meus_livros),
        "meus_livros": livros_paginados
    }

@app.post("/adiciona")
def post_livro(id_livro: int, livro: Livro):
    """
    Adiciona um novo livro à biblioteca.
    """
    if id_livro in meus_livros:
        raise HTTPException(status_code=400, detail="Livro já existe.")

    meus_livros[id_livro] = livro.dict()
    return {"message": "Livro adicionado com sucesso.", "livro": meus_livros[id_livro]}

@app.put("/atualiza/{id_livro}")
def put_livro(id_livro: int, livro: Livro):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")

    meus_livros[id_livro] = livro.dict()
    return {"message": "Livro atualizado com sucesso.", "livro": meus_livros[id_livro]}

@app.delete("/deletar/{id_livro}")
def delete_livro(id_livro: int):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        del meus_livros[id_livro]
        return {"message": "Livro deletado com sucesso."}