from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="API de Gerenciamento de Tarefas",
    description="API RESTful para gerenciar tarefas."
)

banco_de_tarefas = []

class Tarefa(BaseModel):
    nome_tarefa: str
    descricao_tarefa: str
    concluida: bool = False

@app.get("/tarefas")
def listar_tarefas():
    if not banco_de_tarefas:
        raise HTTPException(status_code=404, detail="Nenhuma tarefa encontrada.")
    return banco_de_tarefas


@app.post("/adiciona_tarefa")
def adicionar_tarefa(tarefa: Tarefa):
    titulo = tarefa.nome_tarefa
    descricao = tarefa.descricao_tarefa
    concluida = tarefa.concluida

    banco_de_tarefas.append (tarefa)
    return {"message": "Tarefa adicionada com sucesso.", "tarefa": tarefa }

@app.put("/atualiza_tarefa/{titulo_tarefa}")
def atualizar_tarefa(titulo_tarefa: str, tarefa: Tarefa):
    for i, t in enumerate(banco_de_tarefas):
        if t.nome_tarefa == titulo_tarefa:
            banco_de_tarefas[i] = tarefa
            return {"message": "Tarefa atualizada com sucesso.", "tarefa": tarefa}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada.")

@app.delete("/deletar_tarefa/{titulo_tarefa}")
def deletar_tarefa(titulo_tarefa: str):
    for i, t in enumerate(banco_de_tarefas):
        if t.nome_tarefa == titulo_tarefa:
            del banco_de_tarefas[i]
            return {"message": "Tarefa deletada com sucesso."}
    raise HTTPException(status_code=404, detail="Tarefa não encontrada.")