from typing_extensions import TypedDict, Literal, NotRequired
from langgraph.graph import StateGraph, START, END  
from gateway import Gateway

Categoria=Literal["domanda", "comando", "saluto"]
gateway=Gateway()


class Stato(TypedDict):
    richiesta: str
    categoria: NotRequired[Categoria]
    risposta: NotRequired[str]

def router(stato: Stato) -> str:
    categoria=stato["categoria"]
    return categoria

def classifica_messaggio(stato: Stato) :
    system_prompt="sei un assistente che classifica i messaggi in arrivo in tre categorie: domanda, comando e saluto. rispondi con una sola parola tra le tre categorie, senza spiegazioni, se l'inputo non è nè un saluto ne un comando passalo come domanda, e attento che molti saluti si nascondono dietro domande"
    categoria=gateway.chiama_modello(system_prompt, stato["richiesta"], max_tokens=10)
    categoria=categoria.lower().strip()

    if categoria not in ["domanda", "comando", "saluto"]:
        categoria="domanda"

    return {"categoria": categoria}

def rispondi_domanda(stato: Stato) -> dict:
    system_prompt="sei un assistente che risponde alle domande in arrivo, sii chiaro, fai degli esempi se possibile, e rispondi in modo conciso"
    risposta=gateway.chiama_modello(system_prompt, stato["richiesta"], max_tokens=10)

    return {"risposta": risposta}

def esegui_comando(stato: Stato) -> dict:
    system_prompt="sei un assistente che esegue i comandi in arrivo, sii chiaro, fai degli esempi se possibile, e rispondi in modo conciso"
    risposta=gateway.chiama_modello(system_prompt, stato["richiesta"], max_tokens=10)

    return {"risposta": risposta}

def rispondi_saluto(stato: Stato) -> dict:
    system_prompt="se ti arriva un saluto, rispondi col saluto appropriato"
    risposta=gateway.chiama_modello(system_prompt, stato["richiesta"], max_tokens=10)
    return {"risposta": risposta}


builder=StateGraph(Stato)
builder.add_node("rispondi_domanda", rispondi_domanda)
builder.add_node("esegui_comando", esegui_comando)
builder.add_node("rispondi_saluto", rispondi_saluto)
builder.add_node("classifica_messaggio", classifica_messaggio)

builder.add_conditional_edges(
    "classifica_messaggio", router,
    {
        "domanda": "rispondi_domanda",
        "comando": "esegui_comando",
        "saluto": "rispondi_saluto"
    }
)

builder.add_edge(START, "classifica_messaggio")
builder.add_edge("rispondi_domanda", END)
builder.add_edge("esegui_comando", END)
builder.add_edge("rispondi_saluto", END)

grafo=builder.compile()

risposta=grafo.invoke({"richiesta": "ciao"})

print("categoria: "+ risposta["categoria"]+"\n")
print("Output finale:", risposta["risposta"])