from typing import Literal
from typing_extensions import TypedDict, NotRequired
from gateway import Gateway

Categoria = Literal["python", "generale", "langgraph"]

class Stato(TypedDict):
    domanda: str
    categoria: NotRequired[Categoria]
    risposta: NotRequired[str]

class Classificatore:
    def __init__(self, gateway: Gateway):
        self.gateway=gateway

    def classifica_domanda(self, stato: Stato) -> dict:
        system_prompt="classifica la domanda dell'utente, rispondi esclusivamente con una sola parola: langgraph se riguarda il framework ai, python se riguarda 'python', altrimenti 'generale'"
        user_prompt=stato['domanda']
        classificazione= self.gateway.chiama_modello(system_prompt, user_prompt)

        classificazione=classificazione.lower().strip()

        if classificazione not in ["python", "generale", "langgraph"]:
            classificazione="generale"

        return {"categoria": classificazione}


    def scegli_percorso(self, stato: Stato) -> Categoria:
        return stato["categoria"]

    
    def risposta_python(self, stato: Stato) -> dict:
        system_prompt="sei un tutor python. rispondi in italiano, in modo didattico, includendo un breve esempio di codice se necessario. Rispondi esclusivamente alla domanda dell'utente, senza aggiungere commenti o spiegazioni extra."
        user_prompt= stato["domanda"]
        risposta = self.gateway.chiama_modello(system_prompt, user_prompt)

        return {"risposta": risposta}


    def risposta_generale(self, stato: Stato) -> dict:
        system_prompt="sei un tutor generale. rispondi in italiano, in modo didattico, includendo un breve esempio se necessario. Rispondi esclusivamente alla domanda dell'utente, senza aggiungere commenti o spiegazioni extra."
        user_prompt= stato["domanda"]
        risposta = self.gateway.chiama_modello(system_prompt, user_prompt)

        return {"risposta": risposta}


    def risposta_langgraph(self, stato: Stato) -> dict:
            system_prompt="sei un tutor di AI engineering. rispondi in italiano, in modo didattico, includendo un breve esempio se necessario. Rispondi esclusivamente alla domanda dell'utente, senza aggiungere commenti o spiegazioni extra."
            user_prompt= stato["domanda"]
            risposta = self.gateway.chiama_modello(system_prompt, user_prompt)
    
            return {"risposta": risposta}