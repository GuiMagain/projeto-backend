
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import livraria

DATABASE_URL_TEST = "sqlite://"

engine = create_engine(
    DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


@pytest.fixture(autouse=True)
def preparar_banco_de_teste(monkeypatch):
    livraria.Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()

    livros = [
        livraria.LivroDB(
            nome_livro="A revolução dos bichos",
            autor_livro="George Orwell",
            ano_livro=1945
        )
    ]

    for i in range(9):
        livros.append(
            livraria.LivroDB(
                nome_livro=f"Livro {i}",
                autor_livro="Autor teste",
                ano_livro=2020
            )
        )

    db.add_all(livros)
    db.commit()

    def obter_sessao():
        yield db

    livraria.app.dependency_overrides[livraria.sessao_db] = obter_sessao

    monkeypatch.setattr(livraria.redis_client, "get", lambda chave: None)
    monkeypatch.setattr(livraria.redis_client, "setex", lambda *args: True)

    yield

    livraria.app.dependency_overrides.clear()
    db.close()
    livraria.Base.metadata.drop_all(bind=engine)
