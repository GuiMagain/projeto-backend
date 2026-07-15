from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List

# Inicializa a API
app = FastAPI(
    title="API de Gerenciamento de Biblioteca",
    description="API RESTful para gerenciar livros e empréstimos."
)

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

@app.get("/livros")
def get_livro():
    if not meus_livros:
        raise HTTPException(status_code=404, detail="Nenhum livro encontrado.")
    return meus_livros

@app.post("/adiciona")
def post_livro(id_livro: int, livro: Livro):
    """
    Adiciona um novo livro à biblioteca.
    """
    if id_livro in livros:
        raise HTTPException(status_code=400, detail="Livro já existe.")
    
    meus_livros[id_livro] = livro.dict()
    return {"message": "Livro adicionado com sucesso.", "livro": livros[id_livro]}

@app.put("/atualiza/{id_livro}")
def put_livro(id_livro: int, livro: Livro):
    meu_livro = meus_livros.get(id_livro)
    if not meu_livro:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        meu_livro[id_livro] = livro.dict()
    return {"message": "Livro atualizado com sucesso.", "livro": meu_livro[id_livro]}

@app.delete("/deletar/{id_livro}")
def delete_livro(id_livro: int):
    if id_livro not in meus_livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado.")
    else:
        del meus_livros[id_livro]
        return {"message": "Livro deletado com sucesso."}