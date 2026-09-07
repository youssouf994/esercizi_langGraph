from functools import lru_cache
from openai import OpenAI

class Gateway:
    def __init__(self):
         self.client =OpenAI(base_url="http://172.16.77.153:8080/v1", api_key="nessuna")


    @lru_cache(maxsize=1)
    def get_model_id(self):
        """fa una richiesta al server per ottenere l'elenco dei modelli disponibili e lo salva in cache per evitare una richiesta ad ogni chiamata"""
        modelli= self.client.models.list() 

        if not modelli.data:
            raise ValueError("Nessun modello disponibile, controlla il server")

        return modelli.data[0].id

    def chiama_modello(self, system_prompt: str, user_prompt: str, temperature: float =0.0, max_tokens: int = 10000) -> str:
        response= self.client.chat.completions.create(
            model=self.get_model_id(), 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ], 
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not response.choices:
            raise ValueError("Nessuna risposta dal modello, controlla il server")
        else :
            return response.choices[0].message.content.strip()

        
