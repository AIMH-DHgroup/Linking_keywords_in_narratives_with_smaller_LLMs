from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.llms import Ollama

from json_repair import repair_json
import json
from difflib import SequenceMatcher
import difflib

import time
import os
import re
import logging
import csv

# logger config
logging.basicConfig(filename='error_log_moving.txt', level=logging.ERROR, 
                    format='%(asctime)s - %(levelname)s - %(message)s')


def estrai_json_da_stringa(stringa, percorso_file_json):
    """
    extract the json from a string (from an LLM's answer)
    """
    # regex to extract the JSON from a string
    match = re.search(r'\{.*\}', stringa, re.DOTALL)
    if match:
        json_string = match.group(0)

        
        # removes punctuation marks
        json_string_pulito = re.sub(r',\s*(\}|\])', r'\1', json_string)
        
        try:
            return json.loads(json_string_pulito)
        except json.JSONDecodeError as e:
            # register the issue in the logger
            logging.error(f"Errore nel JSON: {percorso_file_json}")
            logging.error(f"Errore nel parsing del JSON: {e}")
            logging.error(f"Stringa problematica: {json_string_pulito}")
            logging.error(f"###")
            logging.error(f"###")
            logging.error(f"###")
            try:
                good_json_string = repair_json(json_string_pulito)
                logging.error(f"**********")
                logging.error(f"json riparato e inserito nel file")
                logging.error(f"**********")
                return json.loads(good_json_string)
            except:
                logging.error(f"$$$$$$$$$$")
                logging.error(f"json Nemmeno riparato")
                logging.error(f"$$$$$$$$$$")
                return None
    else:
        logging.error(f"Nessun JSON valido trovato nella stringa: {stringa}")
        return None

def aggiorna_file_json(nuovi_dati, percorso_file):
    """
    Create and update the json files of the 30 MOVING narratives with the predictions of the LLMs
    """
    
    if os.path.exists(percorso_file):
        with open(percorso_file, 'r', encoding='utf-8') as file:
            dati_esistenti = json.load(file)
    else:
        dati_esistenti = []

    dati_esistenti.append(nuovi_dati)

    with open(percorso_file, 'w', encoding='utf-8') as file:
        json.dump(dati_esistenti, file, ensure_ascii=False, indent=4)


# prompt approach 1
systemPrompt= """recognize the keywords in the text and, for each of them, find the Wikidata ID. The final result should be a json like this:

### Json
    {
        "keywords": [
            {
                "keyword_in_the_text": "...",
                "wikidata_id": "..."
            },
            {
                "keyword_in_the_text": "...",
                "wikidata_id": "..."
            }
            ...
        ]
    }

Answer only with the json
"""

# prompt approach 2
systemPrompt= """recognize the keywords in the text. The final result should be a json like this:

### Json
    {
        "keywords": [
            {
                "keyword_in_the_text": "..."
            },
            {
                "keyword_in_the_text": "..."
            }
            ...
        ]
    }

Answer only with the json
"""

# prompt approach 3
systemPrompt= """
###keyword's definition 
A keyword is a key element extracted from texts. There are four distinct roles for the keywords: (1) terminology, referring to specialized lexical items within a specific domain; (2) topics, encompassing terms and labels within systematic concept systems like knowledge bases, such as Wikidata; (3) index terms, which highlight major concepts, events, or individuals, including named entities; and (4) summary terms, designed to provide a concise description of the content.

###request
Basing on the provided keyword's definition, recognize the keywords in the text and, for each of them, find the exact title corresponding to the Wikipedia page. The final result should be a json like this:

### Json
    {
        "keywords": [
            {
                "keyword_in_the_text": "...",
                "wikipedia_title": "..."
            },
            {
                "keyword_in_the_text": "...",
                "wikipedia_title": "..."
            }
            ...
        ]
    }

Answer only with the json
"""


directory= "selected_MOVING_narratives/"
listllms= [  "deepseek-r1:14b-qwen-distill-q8_0", "phi4:14b-q8_0", "llama2:13b-chat-q8_0", "llama3:8b-instruct-q8_0", "mistral:7b-instruct-q8_0", "gemma2:9b-instruct-q8_0", "gemma2:2b",  "llama3.2:3b", "phi3.5:latest"]



# cicle all the selected LLMs
for llmModel in listllms:
   
   # cicle all the selected 30 MOVING narratives
    for filename in os.listdir(directory):
        
        if filename.endswith(".csv"):
            filepath = os.path.join(directory, filename)
            
                
            # onep the CSV
            with open(filepath, newline='', encoding='utf-8') as csvfile:
                csvreader = csv.reader(csvfile)
                
                    
                # skip the first line
                next(csvreader)
                    

                for row in csvreader:
                    # get the second column value (textual description)
                    if len(row) > 1:
   
                        sen = row[1]

                        # call Ollama 
                        llm = Ollama(
                            model=llmModel, 
                            system=systemPrompt, 
                            num_ctx=4096, 
                            temperature=0.01, 
                            callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
                        )
                        
                        events = llm(sen)
    
                        # root to save the relut json file
                        os.makedirs("movingJson/"+llmModel, exist_ok=True)
                        percorso_file_json = 'movingJson/'+llmModel+'/'+filename+'.json'
                        
                        # extract json from the answer of the LLM
                        json_estratto = estrai_json_da_stringa(events, percorso_file_json)
                        
                        if json_estratto:
                            
                            # save and update the json
                            aggiorna_file_json(json_estratto, percorso_file_json)
                        else:
                            print("Nessun JSON trovato nella stringa.")
                            my_jsone = {
                                "keywords": []
                                
                            }
                            aggiorna_file_json(my_jsone, percorso_file_json)