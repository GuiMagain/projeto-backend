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
class Livro(BaseModel):
    nome_livro: str
    autor_livro: str
    ano_livro: int

class AtualizarQuantidade(BaseModel):
    quantidade: int

class Emprestimo(BaseModel):
    nome_livro: str
    quantidade: int

# ---------------------------------------------------------
# Rotas (Endpoints) da API
# ---------------------------------------------------------

# 1. Adicionar livro (POST)
@app.post("/livros", status_code=201)
def adicionar_livro(livro: Livro):
    if livro.titulo in livros:
        raise HTTPException(status_code=400, detail="Livro já existe no sistema.")
    
    livros[livro.titulo] = {"autor": livro.autor, "quantidade": livro.quantidade}
    return {"mensagem": f"Livro '{livro.titulo}' adicionado com sucesso!"}

# 2. Listar livros (GET)
@app.get("/livros")
def listar_livros():
    if not livros:
        return {"mensagem": "Nenhum livro cadastrado na biblioteca no momento."}
    
    # Retornando a lista em formato estruturado (JSON)
    lista_formatada = [
        {"titulo": t, "autor": d["autor"], "quantidade": d["quantidade"]}
        for t, d in sorted(livros.items())
    ]
    return {"livros": lista_formatada}

# 3. Remover livro (DELETE)
@app.delete("/livros/{titulo}")
def remover_livro(titulo: str):
    if titulo not in livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado no sistema.")
    
    del livros[titulo]
    return {"mensagem": f"Livro '{titulo}' removido com sucesso!"}

# 4. Atualizar quantidade de livros (PUT)
@app.put("/livros/{titulo}")
def atualizar_quantidade(titulo: str, atualizacao: AtualizarQuantidade):
    if titulo not in livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado no sistema.")
    
    livros[titulo]["quantidade"] = atualizacao.quantidade
    return {"mensagem": f"Quantidade do livro '{titulo}' atualizada para {atualizacao.quantidade}."}

# 5. Registrar empréstimo (POST)
@app.post("/emprestimos")
def registrar_emprestimo(emprestimo: Emprestimo):
    titulo = emprestimo.titulo
    qtd = emprestimo.quantidade

    if titulo not in livros:
        raise HTTPException(status_code=404, detail="Livro não encontrado no sistema.")
    
    if qtd > livros[titulo]["quantidade"]:
        raise HTTPException(status_code=400, detail="Não há exemplares suficientes disponíveis.")
    
    # Deduz a quantidade e registra no histórico
    livros[titulo]["quantidade"] -= qtd
    historico_emprestimos.append({"titulo": titulo, "quantidade": qtd})
    
    return {"mensagem": f"Empréstimo de {qtd} exemplar(es) de '{titulo}' registrado com sucesso!"}

# 6. Exibir histórico de empréstimos (GET)
@app.get("/emprestimos")
def listar_historico_emprestimos():
    if not historico_emprestimos:
        return {"mensagem": "Nenhum empréstimo foi registrado ainda."}
    
    return {"historico": historico_emprestimos}