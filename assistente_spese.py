from typing_extensions import TypedDict, NotRequired
from typing import Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from gateway import Gateway

gateway=Gateway()


class Stato(TypedDict):
    messaggio: str
    importo: float
    budget: NotRequired[float]
    totale_speso: NotRequired[float]
    operazione: Literal["spesa", "riepilogo"]
    risposta: NotRequired[str]


def prepara_stato(stato: Stato)-> dict:
    budget=stato.get("budget", 500.0)
    totale_speso=stato.get("totale_speso", 0.0)

    return {"budget": budget, "totale_speso":totale_speso}

def classifica(stato: Stato)-> dict:
    trovato=False
    iterazioni= 0

    while trovato!=True:
        system_prompt="sei un classificatore di stati langgraph, in base alla domanda che ti arriva capisci se è una 'spesa' oppure un 'riepilogo', rispondi solamante con spesa oppure riepilogo, in italiano e senza nessun carattere speciale, come output vorrei 1 sola parola"
        user_prompt=f"classifica questo prompt: {stato["messaggio"]}"
        stato_compreso=gateway.chiama_modello(system_prompt, user_prompt)
        stato_compreso=stato_compreso.strip().lower()
        iterazioni+=1
        print(stato_compreso)
        
        if ((stato_compreso=="spesa" or stato_compreso=="riepilogo") and iterazioni < 3):
            trovato=True
            return {"operazione": stato_compreso}
        


def registra_spesa(stato: Stato) ->dict:
    stato.get("totale_speso", 0)
    return {"totale_speso": stato["totale_speso"]+ stato["importo"]}

def leggi_riepilogo(stato: Stato) -> dict:
    return dict(stato)

def rispondi(stato: Stato) ->dict:
    disponibilita=stato["budget"] - stato["totale_speso"]
    system_prompt="sei un consulente finanziario, fai un riepilogo sulla base dei dati forniti dall'utente"
    user_prompt=f"""budget mensile:{stato["budget"]}
                totale speso: {stato['totale_speso']}
                disponibilità attuale: {disponibilita}"""

    return {"risposta": gateway.chiama_modello(system_prompt, user_prompt)}

def router(stato: Stato) -> dict:
    return stato["operazione"]


builder=StateGraph(Stato)
checkpointer=InMemorySaver()

builder.add_node("prepara_stato", prepara_stato)
builder.add_node("classifica", classifica)
builder.add_node("registra_spesa", registra_spesa)
builder.add_node("leggi_riepilogo", leggi_riepilogo)
builder.add_node("rispondi", rispondi)

builder.add_conditional_edges(
    "classifica", router,
    {
        "spesa": "registra_spesa",
        "riepilogo": "leggi_riepilogo"
    }
)

builder.add_edge(START, "prepara_stato")
builder.add_edge("prepara_stato", "classifica")
builder.add_edge("registra_spesa", "rispondi")
builder.add_edge("leggi_riepilogo", "rispondi")
builder.add_edge("rispondi", END)

grafo=builder.compile(checkpointer=checkpointer)

config_a={"configurable": {"thread_id": "casa-anna"}}
config_b={"configurable": {"thread_id": "casa-marco"}}

print(grafo.invoke(
    {
        "messaggio": "ho speso 25 euro al supermercato",
        "importo": 25.0,
        "budget": 500
    },
    config=config_a
))


print(grafo.invoke(
    {
        "messaggio": "ho pagato 40 euro di benzina",
        "importo": 40.0
    },
    config=config_a
))


print(grafo.invoke(
    {
        "messaggio": "ho speso 15 euro per il pranzo",
        "importo": 15.0
    },
    config=config_b
))

print(grafo.invoke(
    {
        "messaggio": "quanto mi resta questo mese?"
    },
    config=config_a
))

print(grafo.invoke(
    {
        "messaggio": "fammi un riepilogo delle spese"
    },
    config=config_b
))





