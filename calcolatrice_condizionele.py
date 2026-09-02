from typing_extensions import TypedDict, NotRequired, Literal
from langgraph.graph import START, END, StateGraph

class Stato(TypedDict):
    numero: float
    operazione: Literal["doppio", "quadrato", "negativo"]
    risultato: NotRequired[float]


def doppio(stato: Stato) -> dict:
    return {"risultato": stato["numero"]*2}

def quadrato(stato: Stato) -> dict:
    return {"risultato": stato["numero"]**2}

def negativo(stato: Stato) -> dict:
    return {"risultato" : stato["numero"]- stato["numero"]*2}

def router(stato: Stato) -> str:
    return stato["operazione"]


builder=StateGraph(Stato)
builder.add_node("doppio", doppio)
builder.add_node("quadrato", quadrato)
builder.add_node("negativo", negativo)

builder.add_conditional_edges(
    START, router,
    {
        "doppio": "doppio",
        "quadrato": "quadrato",
        "negativo": "negativo"
    }
)


builder.add_edge("doppio", END)
builder.add_edge("quadrato", END)
builder.add_edge("negativo", END)

grafo=builder.compile()

risultato=grafo.invoke({"numero": 10, "operazione": "doppio"})
print(risultato["numero"], risultato["operazione"], "=", risultato["risultato"])

risultato=grafo.invoke({"numero": 10, "operazione": "quadrato"})
print(risultato["numero"], risultato["operazione"], "=", risultato["risultato"])

risultato=grafo.invoke({"numero": 10, "operazione": "negativo"})
print(risultato["numero"], risultato["operazione"], "=", risultato["risultato"])


