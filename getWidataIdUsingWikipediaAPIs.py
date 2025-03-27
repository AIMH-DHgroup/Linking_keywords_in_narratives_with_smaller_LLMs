import requests
import os
import json

# Use Wikipedia APIs to find Wikidata QID from a Wikipedia title
def get_wikidata_entity_from_wikipedia_title(language, title):
    
    url = f"https://{language}.wikipedia.org/w/api.php"
    
    # Parameters
    params = {
        "action": "query",
        "prop": "pageprops",
        "titles": title,
        "format": "json",
        "redirects": 1  # turn on redirect
    }
    
    # HTTP GET to WIkipedia APIs
    response = requests.get(url, params=params)
    
    data = response.json()
    
    pages = data.get("query", {}).get("pages", {})
    if pages:
        page = next(iter(pages.values()))  # Ottiene il primo risultato
        if "pageprops" in page and "wikibase_item" in page["pageprops"]:
            return page["pageprops"]["wikibase_item"]
        else:
            return None  
    else:
        return None  


# Elaborate the JSON file (LLMs answers)
def process_json(input_json, language='en'):
    output_json = []  
    
    # for each object in the JSON
    for item in input_json:
        new_item = {"keywords": []}  # Nuovo oggetto da popolare
        
        # checks if the key "keywords" exists
        if "keywords" in item:
            for entity in item["keywords"]:
                wikipedia_label = entity.get("wikipedia_title")
                
                keyword_in_the_text = entity.get("keyword_in_the_text")
                
                if wikipedia_label:  # checks if the key "wikipedia_title" exists
                    
                    # call Wikipedia APIs to find Wikidata QID
                    wikidata_id = get_wikidata_entity_from_wikipedia_title(language, wikipedia_label)
                    
                    if wikidata_id: 
                        new_item["keywords"].append({
                            "originalKey": keyword_in_the_text,
                            "original_value": wikipedia_label,
                            "Wikidata_ID": wikidata_id
                        })
        else:
            
            pass
        
        output_json.append(new_item)
    
    return output_json

# Read a JSON file
def read_json_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

# Save result in a JSON file
def save_json_to_file(output_data, output_path):
    with open(output_path, 'w', encoding='utf-8') as file:
        json.dump(output_data, file, indent=4, ensure_ascii=False)

#Elaborate all the JSON files (LLMs answers) in a folder
def process_all_json_files(input_folder, output_folder, language='en'):
    # Get all JSON in the input folder
    for filename in os.listdir(input_folder):
        if filename.endswith(".json"):
            
            input_file_path = os.path.join(input_folder, filename)
            output_file_path = os.path.join(output_folder, filename)  
            
            # read a JSON file input
            try:
                input_json = read_json_from_file(input_file_path)
            except json.JSONDecodeError:
                print(f"Errore nella lettura di {filename}. File JSON non valido.")
                continue
            
            # Elaborate the JSON file to get the ID Wikidata
            output_json = process_json(input_json, language)
            
            # Save results in the output JSON file
            save_json_to_file(output_json, output_file_path)
            print(f"Elaborato {filename} e salvato come {filename}")



process_all_json_files("folder_with_an_LLM_JSONanswers", "otuptu_folder", language='en')