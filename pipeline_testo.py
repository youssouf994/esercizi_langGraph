from typing_extensions import TypedDict, NotRequired
from langgraph.graph import START, END, StateGraph

class Stato(TypedDict):
    testo :str


def pulisci_testo(stato: Stato) -> dict:
    print("nodo pulisci_testo\nentrato: "+ stato["testo"])
    testo_pulito=stato["testo"].strip().replace("\n", " ")
    print("nodo pulisci_testo\nuscito: "+ stato["testo"])

    return {"testo": testo_pulito}

def converti_in_maiuscolo(stato:Stato) -> dict:
    print("nodo converti_in_maiuscolo\nentrato: "+ stato["testo"])
    testo_maiuscolo=stato["testo"].upper()
    print("nodo converti_in_maiuscolo\nuscito: "+ testo_maiuscolo)

    return {"testo": testo_maiuscolo}

def aggiungi_prefisso(stato: Stato) -> dict:
    print("nodo aggiungi_prefisso\nentrato: "+ stato["testo"])
    testo_con_prefisso= "RISULTATO: "+stato["testo"]
    print("nodo aggiungi_prefisso\nuscito: "+ testo_con_prefisso)

    return {"testo": testo_con_prefisso}


builder= StateGraph(Stato)
builder.add_node("pulisci_testo", pulisci_testo)
builder.add_node("converti_in_maiuscolo", converti_in_maiuscolo)
builder.add_node("aggiungi_prefisso", aggiungi_prefisso)

builder.add_edge(START, "pulisci_testo")
builder.add_edge("pulisci_testo", "converti_in_maiuscolo")
builder.add_edge("converti_in_maiuscolo", "aggiungi_prefisso")
builder.add_edge("aggiungi_prefisso", END)

grafo=builder.compile()

output=grafo.invoke({"testo": "    ciao langgraph è fantastico!   \n\n"})

print("grafo completato")
print("Output finale:", output["testo"])
