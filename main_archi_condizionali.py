from langgraph.graph import StateGraph, START, END
from gateway import Gateway
from archi_condizionali import Classificatore, Stato


gateway = Gateway()
classificatore = Classificatore(gateway)

builder = StateGraph(Stato)
builder.add_node("classifica_domanda", classificatore.classifica_domanda)
builder.add_node("risposta_python", classificatore.risposta_python)
builder.add_node("risposta_generale", classificatore.risposta_generale)
builder.add_node("risposta_langgraph", classificatore.risposta_langgraph)

builder.add_edge(START, "classifica_domanda")

builder.add_conditional_edges(
    "classifica_domanda", classificatore.scegli_percorso,
    {
        "python": "risposta_python",
        "generale": "risposta_generale",
        "langgraph": "risposta_langgraph"
    },
)

builder.add_edge("risposta_python", END)
builder.add_edge("risposta_generale", END)
builder.add_edge("risposta_langgraph", END)

graph = builder.compile()

output = graph.invoke({"domanda": "quanti anni ha la regina d'inghilterra?"})

print("categoria:", output["categoria"])
print("risposta:", output["risposta"])
