import time
from celery_app import celery_app

@celery_app.task(name="tasks.somarb", bind=True)
def somar(self, a, b):
    time.sleep(5)
    return a + b 

@celery_app.task(name="tasks.fatorial", bind=True)
def fatorial(self, n):
    time.sleep(5)
    if n < 0:
        raise ValueError("O fatorial não está definido para números negativos.")

    resultado = 1

    for i in range(2, n + 1):
        resultado *= i
    return resultado