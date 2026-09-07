from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver

class Stato(TypedDict):
    testo: str
    totale_parole:NotRequired[int]


def conta_parole(stato: Stato) ->dict:
    conteggio= len(stato["testo"].split())
    precedente= stato.get("totale_parole", 0)
    return {"totale_parole": precedente + conteggio}




builder =StateGraph(Stato)
builder.add_node("conta_parole", conta_parole)
builder.add_edge(START, "conta_parole")
builder.add_edge("conta_parole", END)

checkpointer= InMemorySaver()
grafo=builder.compile(checkpointer=checkpointer)

config_a={"configurable": {"thread_id":"1"}}
config_b={"configurable": {"thread_id":"2"}}

print(grafo.invoke({"testo": "ciao, conteggio"}, config=config_a))
print(grafo.invoke({"testo": "oggi studio langgraph"}, config=config_a))
print(grafo.invoke({"testo": "prima prova"}, config=config_b))
print(grafo.get_state(config=config_a))
print(grafo.get_state(config=config_b))