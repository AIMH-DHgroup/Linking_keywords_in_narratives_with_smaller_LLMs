import urllib.parse
import urllib.request
import json
import os
import csv
import time


def aggiorna_file_json(nuovi_dati, percorso_file):
    """
    Crea/aggiorna i file JSON con le entità restituite dalle API.
    Ogni file JSON contiene una lista di item (uno per riga del CSV).
    """
    # Assicura che la cartella esista
    os.makedirs(os.path.dirname(percorso_file), exist_ok=True)

    if os.path.exists(percorso_file):
        with open(percorso_file, 'r', encoding='utf-8') as file:
            try:
                dati_esistenti = json.load(file)
            except json.JSONDecodeError:
                dati_esistenti = []
    else:
        dati_esistenti = []

    dati_esistenti.append(nuovi_dati)

    with open(percorso_file, 'w', encoding='utf-8') as file:
        json.dump(dati_esistenti, file, ensure_ascii=False, indent=4)


def get_wikidata_id_from_dbpedia(dbpedia_uri, cache, sparql_endpoint="https://dbpedia.org/sparql"):
    """
    Dato un URI DBpedia, interroga il SPARQL endpoint per trovare l'ID Wikidata (owl:sameAs).

    Usa una cache 'dbpedia_uri -> wikidata_id' per evitare chiamate duplicate.
    Restituisce una stringa tipo 'Q76' oppure 'null' se non trovato.
    """
    if dbpedia_uri in cache:
        return cache[dbpedia_uri]

    # SPARQL: cerchiamo i link owl:sameAs che puntano a Wikidata
    query = f"""
    SELECT ?wikidata WHERE {{
      <{dbpedia_uri}> <http://www.w3.org/2002/07/owl#sameAs> ?wikidata .
      FILTER(STRSTARTS(STR(?wikidata), "http://www.wikidata.org/entity/"))
    }}
    LIMIT 1
    """

    params = {
        "query": query,
        "format": "application/sparql-results+json"
    }

    url = sparql_endpoint + "?" + urllib.parse.urlencode(params)

    try:
        with urllib.request.urlopen(url, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"Errore SPARQL per {dbpedia_uri}: {e}")
        cache[dbpedia_uri] = "null"
        return "null"

    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        cache[dbpedia_uri] = "null"
        return "null"

    wikidata_uri = bindings[0]["wikidata"]["value"]
    # wikidata_uri è tipo "http://www.wikidata.org/entity/Q76"
    wikidata_id = wikidata_uri.rsplit("/", 1)[-1]

    cache[dbpedia_uri] = wikidata_id
    return wikidata_id


def CallDBpediaSpotlight(text, lang="en", confidence=0.4, support=20, wikidata_cache=None):
    """
    Chiama l'API di DBpedia Spotlight per annotare il testo e 
    restituisce un dict del tipo: { "keywords": [ ... ] }

    Per ogni entità:
      - originalKey  = surface form nel testo originale
      - original_value = label (titolo) derivata dall'URI DBpedia
      - DBpedia_URI = URI DBpedia della risorsa
      - Wikidata_ID = ID Wikidata (Qxxx) se trovato, altrimenti "null"
    """
    if wikidata_cache is None:
        wikidata_cache = {}

    # Oggetto richiesto: mantiene la compatibilità col tuo codice originale
    new_item = {"keywords": []}

    # Endpoint DBpedia Spotlight per lingua (en, it, ecc.)
    # Esempio: https://api.dbpedia-spotlight.org/en/annotate
    spotlight_url = f"https://api.dbpedia-spotlight.org/{lang}/annotate"

    data = urllib.parse.urlencode({
        "text": text,
        "confidence": str(confidence),
        "support": str(support)
    }).encode("utf-8")

    headers = {
        "Accept": "application/json"
    }

    req = urllib.request.Request(spotlight_url, data=data, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=60) as f:
            response_bytes = f.read()
            response = json.loads(response_bytes.decode("utf-8"))
    except Exception as e:
        print(f"Errore DBpedia Spotlight sul testo '{text[:50]}...': {e}")
        return new_item  # ritorna oggetto vuoto, ma valido

    resources = response.get("Resources", [])
    if not isinstance(resources, list):
        # A volte se c'è una sola risorsa la API restituisce un dict singolo
        resources = [resources]

    for res in resources:
        dbpedia_uri = res.get("@URI")
        surface_form = res.get("@surfaceForm", "")

        if not dbpedia_uri:
            continue

        # Ricava una label leggibile dall'URI (ultima parte, con underscore -> spazi)
        label = urllib.parse.unquote(dbpedia_uri.rsplit("/", 1)[-1]).replace("_", " ")

        # Prende l'ID Wikidata via SPARQL
        wikidata_id = get_wikidata_id_from_dbpedia(dbpedia_uri, wikidata_cache)

        entity = {
            "originalKey": surface_form,
            "original_value": label,
            "DBpedia_URI": dbpedia_uri,
            "Wikidata_ID": wikidata_id if wikidata_id is not None else "null"
        }

        new_item["keywords"].append(entity)
        
    
    seen = set()
    unique_entities = []
    for ent in new_item["keywords"]:
        key = (ent["originalKey"], ent["Wikidata_ID"])
        if key not in seen:
            seen.add(key)
            unique_entities.append(ent)

    new_item["keywords"] = unique_entities

    return new_item


# ==========================
# PARAMETRI E CICLO PRINCIPALE
# ==========================

# Cartella con i CSV
directory = "../selected_MOVING_narratives"

# Cartella di output per i JSON
percorso_file_json_da_salvare = "baseline_data_output"

# lingua per DBpedia Spotlight: "en", "it", ecc.
spotlight_lang = "en"  

# cache in memoria per non chiamare il SPARQL endpoint più volte per lo stesso URI
wikidata_cache = {}

# per tutti i CSV nella cartella
for filename in os.listdir(directory):

    if not filename.endswith(".csv"):
        continue

    filepath = os.path.join(directory, filename)

    # Nome file JSON: togliamo .csv e mettiamo .json
    base_name, _ = os.path.splitext(filename)
    json_output_path = os.path.join(percorso_file_json_da_salvare, base_name + ".csv.json")

    with open(filepath, newline='', encoding='utf-8') as csvfile:
        csvreader = csv.reader(csvfile)

        # salta l'intestazione
        next(csvreader, None)

        for row in csvreader:
            # seconda colonna: descrizione testuale
            if len(row) <= 1:
                continue

            sen = row[1].strip()
            if not sen:
                continue

            # chiamata a DBpedia Spotlight
            json_data = CallDBpediaSpotlight(
                sen,
                lang=spotlight_lang,
                confidence=0.5,
                support=20,
                wikidata_cache=wikidata_cache
            )

            # aggiorna/salva il JSON
            aggiorna_file_json(json_data, json_output_path)

            # piccola pausa per non stressare le API
            time.sleep(0.3)
