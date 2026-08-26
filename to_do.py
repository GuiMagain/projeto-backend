from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets 
import os

app = FastAPI(
    title="API de Gerenciamento de Tarefas",
    description="API RESTful para gerenciar tarefas."
)

MEU_USUARIO = "admin"
MINHA_SENHA = "12345678"

security = HTTPBasic()

banco_de_tarefas = []

class Tarefa(BaseModel):
    nome_tarefa: str
    descricao_tarefa: str
    concluida: bool = False

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
def listar_tarefas(page: int=1, size: int=10, ordenar_por: str=None, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    if page < 1 or size <1:
        raise HTTPException(status_code=400, detail="page ou size estão com valores inválidos. Devemser maiores que 0.")

    if not banco_de_tarefas:
        raise HTTPException(status_code=404, detail="Nenhuma tarefa encontrada.")

    if ordenar_por is not None:
        campos_permitidos = ["nome_tarefa", "descricao_tarefa", "concluida"]
        if ordenar_por not in campos_permitidos:
            raise HTTPException(status_code=400, detail="Campo inválido.")

    tarefas_ordenadas = sorted(banco_de_tarefas.items(), key=lambda x: x[0])
    if ordenar_por is not None: 
        tarefas_ordenadas = sorted(banco_de_tarefas.items(), key=lambda x: x[1][ordenar_por])

    start = (page - 1) * size
    end = start + size

    tarefas_paginadas = [
        {"id" : id_tarefa, "nome_tarefa": tarefa_data["nome_tarefa"], "descricao_tarefa": tarefa_data["descricao_tarefa"], "concluida": tarefa_data["concluida"]}
        for id_tarefa, tarefa_data in tarefas_ordenadas[start:end]
    ]
    return {
        "page": page,
        "size": size,
        "total": len(banco_de_tarefas),
        "banco_tarefas": tarefas_paginadas
    }

@app.post("/adiciona_tarefa")
def adicionar_tarefa(tarefa: Tarefa, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    titulo = tarefa.nome_tarefa
    descricao = tarefa.descricao_tarefa
    concluida = tarefa.concluida

    banco_de_tarefas.append (tarefa)
    return {"message": "Tarefa adicionada com sucesso.", "tarefa": tarefa }

@app.put("/atualiza_tarefa/{titulo_tarefa}")
def atualizar_tarefa(titulo_tarefa: str, tarefa: Tarefa, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    for i, t in enumerate(banco_de_tarefas):
        if t.nome_tarefa == titulo_tarefa:
            banco_de_tarefas[i] = tarefa
            return {"message": "Tarefa atualizada com sucesso.", "tarefa": tarefa}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

@app.delete("/deletar_tarefa/{titulo_tarefa}")
def deletar_tarefa(titulo_tarefa: str, credentials: HTTPBasicCredentials = Depends(autenticar_usuario)):
    for i, t in enumerate(banco_de_tarefas):
        if t.nome_tarefa == titulo_tarefa:
            del banco_de_tarefas[i]
            return {"message": "Tarefa deletada com sucesso."}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada.")