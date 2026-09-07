from typing_extensions import TypedDict, NotRequired
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from gateway import Gateway


gateway=Gateway()

class Stato(TypedDict):
    domanda: str
    materia: NotRequired[str]
    risposta: NotRequired[str]
    numero_domande: NotRequired[int]

def prepara_domanda(stato: Stato)-> dict:
    materia=stato.get("materia", "cultura generale")
    conteggio_domande=stato.get("numero_domande", 0)

    return {"materia": materia, "numero_domande": conteggio_domande +1}

def rispondi(stato:Stato) -> dict:
    
    materia=stato.get("materia")
    system_prompt=f"sei un tutor di {materia}, rispondi in italiano in modod breve e didattico"
    user_prompt=stato.get("domanda")
    return {"risposta": gateway.chiama_modello(system_prompt, user_prompt, max_tokens=300)}




builder=StateGraph(Stato)
checkpointer=InMemorySaver()

builder.add_node("rispondi", rispondi)
builder.add_node("prepara_domanda", prepara_domanda)

builder.add_edge(START, "prepara_domanda")
builder.add_edge("prepara_domanda", "rispondi")
builder.add_edge("rispondi", END)

grafo=builder.compile(checkpointer)
config_a={"configurable": {"thread_id": "a"}}
config_b={"configurable": {"thread_id": "b"}}
config_c={"configurable": {"thread_id": "c"}}

print(grafo.invoke({"materia": "python", "domanda": "che cosa sono le liste?"}, config=config_a))
stato=grafo.get_state(config_a)
print("materia: "+stato.values["materia"]+"\nnumero domande: "+str(stato.values["numero_domande"])+"\nrisposta: "+stato.values["risposta"])

print(grafo.invoke({"domanda": "che cosa sono i dizionari?"}, config=config_a))
stato=grafo.get_state(config_a)
print("materia: "+stato.values["materia"]+"\nnumero domande: "+str(stato.values["numero_domande"])+"\nrisposta: "+stato.values["risposta"])

print(grafo.invoke({"materia": "storia", "domanda": "chi era guilio cesare?"}, config=config_b))
stato=grafo.get_state(config_b)
print("materia: "+stato.values["materia"]+"\nnumero domande: "+str(stato.values["numero_domande"])+"\nrisposta: "+stato.values["risposta"])

print(grafo.invoke({"materia": "langgraph", "domanda": "a cosa serve lo stato?"}, config=config_a))
stato=grafo.get_state(config_a)
print("materia: "+stato.values["materia"]+"\nnumero domande: "+str(stato.values["numero_domande"])+"\nrisposta: "+stato.values["risposta"])

print(grafo.invoke({"domanda": "a cosa serve un nodo?"}, config=config_a))
stato=grafo.get_state(config_a)
print("materia: "+stato.values["materia"]+"\nnumero domande: "+str(stato.values["numero_domande"])+"\nrisposta: "+stato.values["risposta"])

print(grafo.invoke({"domanda": "di che colore è il cielo?"}, config=config_c))
stato=grafo.get_state(config_c)
print("materia: "+stato.values["materia"]+"\nnumero domande: "+str(stato.values["numero_domande"])+"\nrisposta: "+stato.values["risposta"])