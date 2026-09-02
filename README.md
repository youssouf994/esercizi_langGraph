# Percorso introduttivo a LangGraph

Questo progetto raccoglie i primi esercizi svolti per imparare LangGraph in
Python. L'obiettivo di questa fase e capire come costruire grafi sequenziali e
condizionali, come far circolare uno stato tra i nodi e come integrare un
modello locale senza mescolare la comunicazione HTTP con la logica del grafo.

Gli argomenti affrontati finora sono:

- stato condiviso;
- nodi e aggiornamenti parziali;
- archi sequenziali;
- routing condizionale;
- compilazione e invocazione del grafo;
- integrazione con un modello servito da `llama-server`;
- separazione del client del modello tramite un gateway;
- normalizzazione e validazione dell'output di un LLM.

## Installazione

Il progetto utilizza Python, LangGraph e il client OpenAI-compatible:

```powershell
python -m pip install -U langgraph openai
```

Gli esercizi che interrogano il modello richiedono un `llama-server` attivo.
Il server usato durante il percorso e stato avviato con un modello Qwen locale:

```powershell
.\build\bin\Release\llama-server.exe `
  -m qwen2.5-coder-7b-instruct-q4_k_m.gguf `
  -ngl 22 `
  -c 8192 `
  --host 0.0.0.0 `
  --port 8080
```

Per verificare che il server sia disponibile:

```powershell
curl.exe http://172.16.77.153:8080/health
curl.exe http://172.16.77.153:8080/v1/models
```

Se client e server sono sullo stesso computer e preferibile usare
`127.0.0.1`. Esporre il server su `0.0.0.0` senza autenticazione lo rende
raggiungibile dagli altri dispositivi ammessi sulla rete.

## Concetti fondamentali

### Stato

Lo stato e la struttura dati condivisa durante una singola esecuzione del
grafo. In questi esercizi viene descritto con `TypedDict`:

```python
from typing_extensions import TypedDict


class Stato(TypedDict):
    numero: int
    risultato: int
```

Ogni nodo riceve lo stato corrente. Lo stato permette ai nodi di comunicare
senza chiamarsi direttamente e senza dipendere dalle variabili locali degli
altri nodi.

`NotRequired` indica che un campo puo non esistere nell'input iniziale perche
verra prodotto durante l'esecuzione:

```python
from typing_extensions import NotRequired


class Stato(TypedDict):
    numero: float
    risultato: NotRequired[float]
```

### Nodi

Un nodo e una normale funzione Python. Riceve lo stato e restituisce un
dizionario contenente soltanto i campi che vuole aggiornare:

```python
def raddoppia(stato: Stato) -> dict:
    return {"risultato": stato["numero"] * 2}
```

Il dizionario restituito non sostituisce tutto lo stato. LangGraph applica
l'aggiornamento allo stato esistente. Per questo, dopo il nodo, `numero` e
ancora presente insieme al nuovo valore di `risultato`.

Un nodo successivo deve leggere il campo aggiornato dal nodo precedente. Per
esempio, dopo `raddoppia`, il nodo `aggiungi_dieci` deve usare
`stato["risultato"]`, non `stato["numero"]`.

### Archi, START ed END

Gli archi definiscono l'ordine di esecuzione:

```python
builder.add_edge(START, "raddoppia")
builder.add_edge("raddoppia", "aggiungi_dieci")
builder.add_edge("aggiungi_dieci", END)
```

`START` rappresenta l'ingresso virtuale del grafo. `END` rappresenta la sua
terminazione. I nodi svolgono il lavoro; gli archi stabiliscono dove proseguire.

### Costruzione, compilazione e invocazione

La costruzione di un grafo segue sempre questi passaggi:

```python
builder = StateGraph(Stato)
builder.add_node("raddoppia", raddoppia)
builder.add_edge(START, "raddoppia")
builder.add_edge("raddoppia", END)

grafo = builder.compile()
output = grafo.invoke({"numero": 5, "risultato": 0})
```

`StateGraph` e il builder: serve a dichiarare la struttura. `compile()` deve
essere chiamato dopo aver aggiunto tutti i nodi e gli archi e produce il grafo
eseguibile. `invoke()` avvia una singola esecuzione con lo stato iniziale e
restituisce lo stato finale.

### Routing condizionale

Un router legge lo stato e restituisce una destinazione:

```python
def router(stato: Stato) -> str:
    return stato["operazione"]
```

Il collegamento condizionale associa ogni possibile risultato del router a un
nodo:

```python
builder.add_conditional_edges(
    START,
    router,
    {
        "doppio": "doppio",
        "quadrato": "quadrato",
        "negativo": "negativo",
    },
)
```

Il router deve decidere il percorso, non modificare lo stato. I nodi di
destinazione eseguono invece il calcolo o producono la risposta.

`Literal` descrive l'insieme dei valori ammessi:

```python
from typing import Literal

Operazione = Literal["doppio", "quadrato", "negativo"]
```

Per un router e preferibile usare l'alias anche come tipo restituito, per
rendere esplicite le destinazioni possibili.

## Integrazione con il modello locale

`llama-server` espone endpoint compatibili con le API OpenAI, tra cui
`/v1/chat/completions`. Il client Python `OpenAI` richiede una stringa non vuota
nel parametro `api_key`, anche quando il server locale non usa autenticazione:

```python
OpenAI(
    base_url="http://172.16.77.153:8080/v1",
    api_key="nessuna",
)
```

In questo caso `nessuna` e soltanto un valore fittizio richiesto dal client. Non
e una chiave reale.

### Il Gateway

Il file `gateway.py` isola la comunicazione con il modello. Il grafo non deve
conoscere URL, endpoint o formato della risposta HTTP; i nodi chiamano soltanto:

```python
gateway.chiama_modello(system_prompt, user_prompt)
```

Questa separazione assegna responsabilita chiare:

- `Gateway` gestisce il client e la comunicazione con `llama-server`;
- i nodi costruiscono i prompt e aggiornano lo stato;
- il router sceglie il prossimo nodo;
- il file principale costruisce e avvia il grafo.

`get_model_id()` interroga `/v1/models` e usa `lru_cache` per evitare di ripetere
la stessa richiesta a ogni chiamata.

### Output probabilistico e routing deterministico

L'output di un LLM non deve essere usato direttamente come destinazione. Anche
con un prompt che chiede una sola parola, il modello potrebbe restituire
`"Saluto"`, `"saluto."`, spazi aggiuntivi oppure una frase completa.

Prima del routing occorre normalizzare e validare:

```python
categoria = categoria.lower().strip()

if categoria not in {"domanda", "comando", "saluto"}:
    categoria = "domanda"
```

Il modello propone una classificazione; il programma controlla che quella
classificazione sia ammessa. Solo dopo la validazione il router puo usarla.

Per una classificazione composta da una sola parola, `max_tokens=10` e
appropriato. Le risposte finali richiedono invece un limite piu ampio: usare
`max_tokens=10` anche nei nodi di risposta puo troncare il testo generato.

## Esercizi svolti

### 1. Raddoppio e somma

File: `langGraph.py`

Grafo:

```text
START -> raddoppia -> aggiungi_dieci -> END
```

Il primo nodo legge `numero` e scrive `risultato`. Il secondo legge il nuovo
`risultato` e aggiunge dieci. L'esercizio ha mostrato che ogni nodo vede lo
stato prodotto dal passaggio precedente.

Errore incontrato: inizialmente `aggiungi_dieci` leggeva `numero`. In questo
modo ignorava il risultato del raddoppio. La correzione e stata leggere
`stato["risultato"]`. Anche l'ultimo arco deve partire da `aggiungi_dieci`, non
da `raddoppia`.

### 2. Pipeline di testo

File: `pipeline_testo.py`

Grafo:

```text
START -> pulisci_testo -> converti_in_maiuscolo -> aggiungi_prefisso -> END
```

I tre nodi aggiornano in sequenza lo stesso campo `testo`. L'output atteso per
`"   ciao langgraph   "` e:

```text
RISULTATO: CIAO LANGGRAPH
```

L'esercizio consolida gli aggiornamenti sequenziali. Un dettaglio ancora da
correggere e il log di uscita di `pulisci_testo`: stampa `stato["testo"]`, cioe
il valore precedente, invece della variabile `testo_pulito`.

Nel testo di prova compare inoltre `Ã¨`, segno che il file e stato salvato o
letto con una codifica errata. I sorgenti dovrebbero essere salvati in UTF-8.

### 3. Calcolatrice condizionale

File: `calcolatrice_condizionele.py`

Grafo:

```text
                 +-> doppio ----+
START -> router -+-> quadrato ---+-> END
                 +-> negativo ---+
```

Il campo `operazione` determina il nodo da eseguire. Le prove svolte producono:

```text
10 doppio = 20
10 quadrato = 100
10 negativo = -10
```

Il router legge soltanto `operazione`, mentre ciascun nodo scrive `risultato`.
La formula `numero - numero * 2` produce correttamente l'opposto, ma `-numero`
esprime la stessa intenzione in modo piu diretto.

### 4. Tutor con categorie Python, generale e LangGraph

File: `archi_condizionali.py` e `main_archi_condizionali.py`

Grafo:

```text
START -> classifica_domanda -> scegli_percorso
                                  |
                     +------------+------------+
                     |            |            |
                     v            v            v
              risposta_python  risposta_   risposta_langgraph
                                generale
                     |            |            |
                     +------------+------------+
                                  |
                                 END
```

`classifica_domanda` interroga il modello e salva `categoria`. Il metodo
`scegli_percorso` non richiama il modello: legge la categoria gia presente
nello stato. I nodi finali usano prompt diversi per produrre risposte
specializzate.

Errori incontrati:

- `api_key=""` non era accettato dal client OpenAI; e stato usato un valore
  fittizio non vuoto;
- `Stato["categoria"]` non e un'annotazione di ritorno valida; e stato creato
  l'alias `Categoria = Literal[...]`;
- il `return` della classificazione era dentro l'`if`, quindi una categoria
  valida causava un ritorno implicito di `None`;
- una risposta generata correttamente non e necessariamente vera: il grafo puo
  funzionare mentre il modello fornisce una spiegazione tecnicamente imprecisa.

### 5. Classificatore domanda, comando e saluto

File: `classificatore2.py`

Grafo:

```text
START -> classifica_messaggio -> router
                                     |
                    +----------------+----------------+
                    |                |                |
                    v                v                v
           rispondi_domanda   esegui_comando   rispondi_saluto
                    |                |                |
                    +----------------+----------------+
                                     |
                                    END
```

Le classificazioni verificate sono:

```text
"Come funziona una lista Python?" -> domanda
"Scrivi una funzione Python"      -> comando
"Ciao, come stai?"                -> saluto
```

Questo esercizio applica correttamente `lower()`, `strip()` e un fallback a
`domanda` per categorie non valide. Rimangono due miglioramenti:

- correggere la codifica del prompt, che contiene `nÃ¨`;
- mantenere `max_tokens=10` nel solo nodo di classificazione e concedere piu
  token ai nodi che devono generare una risposta completa.

## Errori da ricordare

1. Leggere il campo sbagliato significa ignorare l'aggiornamento del nodo
   precedente.
2. Tutti i nodi e gli archi devono essere aggiunti prima di `compile()`.
3. L'ultimo arco deve partire dall'ultimo nodo reale del percorso.
4. Un router sceglie la destinazione; non dovrebbe aggiornare lo stato.
5. Il testo prodotto da un LLM va normalizzato e validato prima di controllare
   il flusso del programma.
6. Un grafo eseguito senza errori non garantisce che la risposta dell'LLM sia
   corretta dal punto di vista dei contenuti.
7. I limiti di generazione devono essere proporzionati al compito: pochi token
   per un'etichetta, piu token per una spiegazione.
8. I file sorgente e i prompt devono usare una codifica coerente, preferibilmente
   UTF-8.

## Esecuzione

Gli esercizi senza modello possono essere avviati direttamente:

```powershell
python .\langGraph.py
python .\pipeline_testo.py
python .\calcolatrice_condizionele.py
```

Con `llama-server` attivo, si possono eseguire anche:

```powershell
python .\main_archi_condizionali.py
python .\classificatore2.py
```

