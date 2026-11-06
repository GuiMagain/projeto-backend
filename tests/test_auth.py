from fastapi.testclient import TestClient
from livraria import app
import os
import pytest

client = TestClient(app)

os.environ["MEU_USUARIO"] = "guimbrum"
os.environ["MINHA_SENHA"] = "1234Gui"

@pytest.fixtures(autouse=True)
def mock_redis(mocker):
    mock_redis_client = mocker.patch("main.redis_client", autospec=True)
    mock_redis_client.get.return_value = None


def test_autenticacao_usuario_com_sucesso():
    response = client.get(
        "/livros",
        auth=("guimbrum", "1234Gui")
    )

    assert response.status_code == 200

def test_autenticacao_usuario_erro():
    response = client.get(
        "/livros",
        auth=("usuario_incorreto", "admin")
    )

    assert response.status_code ==401
    assert response.json()["detail"] == "Usuário ou senha inválidos."

def test_autenticacao_senha_com_erro():
    response = client.get(
        "/livros",
        auth=("guimbrum", "admin")
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Usuário ou senha inválidos."
