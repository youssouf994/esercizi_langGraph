from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END

class Stato(TypedDict):
    numero: int
    risultato: int

def raddoppia(stato: Stato) -> dict:
    valore = stato["numero"]*2
    return {"risultato":valore}

def aggiungi_dieci(stato: Stato) -> dict:
    return {"risultato":stato["risultato"]+10}




builder = StateGraph(Stato)
builder.add_node("raddoppia", raddoppia)
builder.add_node("aggiungi_dieci", aggiungi_dieci)

builder.add_edge(START, "raddoppia")
builder.add_edge("raddoppia", "aggiungi_dieci")
builder.add_edge("aggiungi_dieci", END)

graph = builder.compile()

output=graph.invoke({"numero": 35, "risultato":0,})

print(output)