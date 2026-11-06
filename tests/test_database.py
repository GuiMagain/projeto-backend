
from fastapi.testclient import TestClient
from livraria import app

client = TestClient(app)


def test_get_books():
    response = client.get(
        "/livros",
        auth=("guimbrum", "1234Gui")
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["livros"]) == 10
    assert data["livros"][0]["nome_livro"] == "A revolução dos bichos"
    assert data["livros"][0]["autor_livro"] == "George Orwell"
    assert data["livros"][0]["ano_livro"] == 1945
