import os
import json

def jaccard_similarity(str1, str2):
    """
    Calculate the Jaccard infex between two string.
    """
    set1, set2 = set(str1.lower().split()), set(str2.lower().split())
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    return intersection / union if union != 0 else 0

def extract_wikidata_id(link, nullTP =False):
    """
    Get Wikidata ID from the gold standard keywords Wikidata link
    """
    if nullTP == True:
        if not link:
            return None
        id_part = link.split("/")[-1]
        return None if id_part.lower() == "null" else id_part
    else:
        return link.split("/")[-1] if link else None

def load_json_files(folder_path):
    """
    Load all JSON files from a folder.
    """
    data = {}
    if not os.path.isdir(folder_path):
        return data
    for filename in os.listdir(folder_path):
        if filename.endswith(".json"):
            try:
                with open(os.path.join(folder_path, filename), "r", encoding="utf-8") as file:
                    data[filename] = json.load(file)
            except (json.JSONDecodeError, OSError) as e:
                print(f"Errore nel caricamento del file {filename}: {e}")
    return data

def calculate_metrics(gold_data, predicted_data, jaccard_threshold, nullTP= False):
    """
    Calculate precision, recall e F1 score for keyword extraction and keyword linking.
    """
    # Metriche per keyword extraction
    entity_true_positive = 0
    entity_false_positive = 0
    entity_false_negative = 0

    # Metriche globali per l'keyword linking
    linking_true_positive_global = 0
    linking_false_positive_global = 0
    linking_false_negative_global = 0

    true_positives_per_file = {}

    for filename, gold_content in gold_data.items():
        predicted_content = predicted_data.get(filename.replace(".json", ".csv.json"))
        if not predicted_content:
            continue

        file_true_positive = []

        for gold_entities, pred_entities in zip(gold_content, predicted_content):
            gold_labels = [(entity["Wikipedia_label"], extract_wikidata_id(entity["Wikidata_ID"], nullTP)) for entity in gold_entities["entities"]]
            pred_entities_processed = [
                (entity["originalKey"], entity["Wikidata_ID"]) for entity in pred_entities["entities"]
            ]

            matched_gold = set()
            matched_pred = set()

            for i, (gold_label, gold_wikidata_id) in enumerate(gold_labels):
                for j, (pred_key, pred_wikidata_id) in enumerate(pred_entities_processed):
                    if jaccard_similarity(gold_label, pred_key) >= jaccard_threshold:
                        matched_gold.add(i)
                        matched_pred.add(j)
                        entity_true_positive += 1
                        file_true_positive.append({
                            "gold_label": gold_label,
                            "pred_key": pred_key,
                            "gold_wikidata_id": gold_wikidata_id,
                            "pred_wikidata_id": pred_wikidata_id
                        })

                        # Entity linking (globale): considera ogni entità predetta
                        if gold_wikidata_id == pred_wikidata_id:
                            linking_true_positive_global += 1

            entity_false_negative += len(gold_labels) - len(matched_gold)
            entity_false_positive += len(pred_entities_processed) - len(matched_pred)

            for _, pred_wikidata_id in pred_entities_processed:
                if all(pred_wikidata_id != gold_id for _, gold_id in gold_labels):
                    linking_false_positive_global += 1
            linking_false_negative_global += len(gold_labels) - len(matched_gold)

        true_positives_per_file[filename] = file_true_positive

    # Metrichs for keyword extraction
    entity_precision = entity_true_positive / (entity_true_positive + entity_false_positive) if (entity_true_positive + entity_false_positive) > 0 else 0
    entity_recall = entity_true_positive / (entity_true_positive + entity_false_negative) if (entity_true_positive + entity_false_negative) > 0 else 0
    entity_f1_score = (2 * entity_precision * entity_recall) / (entity_precision + entity_recall) if (entity_precision + entity_recall) > 0 else 0

    # Metrichs for keyword linking
    linking_precision_global = linking_true_positive_global / (linking_true_positive_global + linking_false_positive_global) if (linking_true_positive_global + linking_false_positive_global) > 0 else 0
    linking_recall_global = linking_true_positive_global / (linking_true_positive_global + linking_false_negative_global) if (linking_true_positive_global + linking_false_negative_global) > 0 else 0
    linking_f1_score_global = (2 * linking_precision_global * linking_recall_global) / (linking_precision_global + linking_recall_global) if (linking_precision_global + linking_recall_global) > 0 else 0

    return (entity_precision, entity_recall, entity_f1_score, 
            linking_precision_global, linking_recall_global, linking_f1_score_global, 
            true_positives_per_file)

def process_folders_recursively(gold_folder, root_folder, jaccard_threshold, stampaTP):
    """
    Process all subfolders and calculate metrichs on all the JSON files in the subfolders.
    """
    for dirpath, dirnames, filenames in os.walk(root_folder):
        # Controlla se la cartella contiene file JSON
        json_files = [f for f in filenames if f.endswith(".json")]
        if not json_files:
            continue

        print(f"\nProcessando cartella: {dirpath}")
        predicted_data = load_json_files(dirpath)
        gold_data = load_json_files(gold_folder)

        if not gold_data or not predicted_data:
            print(f"Cartella {dirpath}: Nessun file JSON valido trovato.")
            continue

        try:
            metrics = calculate_metrics(gold_data, predicted_data, jaccard_threshold)
            (entity_precision, entity_recall, entity_f1_score, 
             linking_precision_global, linking_recall_global, linking_f1_score_global, 
             true_positives_per_file) = metrics

            # Stampa i risultati
            print(f"Entity Extraction - Precision: {entity_precision:.4f}")
            print(f"Entity Extraction - Recall: {entity_recall:.4f}")
            print(f"Entity Extraction - F1 Score: {entity_f1_score:.4f}")

            print(f"\nEntity Linking (Globale) - Precision: {linking_precision_global:.4f}")
            print(f"Entity Linking (Globale) - Recall: {linking_recall_global:.4f}")
            print(f"Entity Linking (Globale) - F1 Score: {linking_f1_score_global:.4f}")


            if stampaTP:
                if stampaTP_NER == 1:
                    print("\nTrue Positives per keyword extraction:")
                    for filename, true_positives in true_positives_per_file.items():
                        print(f"\nFile: {filename}")
                        for tp in true_positives:
                            print(f"  Gold Label: {tp['gold_label']} | Predicted Key: {tp['pred_key']}")
                            print(f"    Gold Wikidata ID: {tp['gold_wikidata_id']} | Predicted Wikidata ID: {tp['pred_wikidata_id']}")
                elif stampaTP_EL == 1:
                    print("\nTrue Positives per keyword Linking:")
                    for filename, true_positives in true_positives_per_file.items():
                        print(f"\nFile: {filename}")
                        for tp in true_positives:
                            # Verifica se sia il testo che l'ID Wikidata sono uguali
                            if tp['gold_wikidata_id'] == tp['pred_wikidata_id']:
                                print(f"  Gold Label: {tp['gold_label']} | Predicted Key: {tp['pred_key']}")
                                print(f"    Gold Wikidata ID: {tp['gold_wikidata_id']} | Predicted Wikidata ID: {tp['pred_wikidata_id']}")
          

        except Exception as e:
            #print(f"Errore durante il calcolo delle metriche per la cartella {dirpath}: {e}")
            a=9


def sort_metrics(root_folder, gold_folder, metric_type):
    """
    Sort precision, recall e F1 score calculated for each folder, order by f1 score for the keyword extraction and keyword linking.
    """
    metrics_list = []

    for dirpath, _, filenames in os.walk(root_folder):
        json_files = [f for f in filenames if f.endswith(".json")]
        if not json_files:
            continue

        predicted_data = load_json_files(dirpath)
        gold_data = load_json_files(gold_folder)

        if not gold_data or not predicted_data:
            continue

        try:
            metrics = calculate_metrics(gold_data, predicted_data, 1)
            (entity_precision, entity_recall, entity_f1_score, 
             linking_precision_global, linking_recall_global, linking_f1_score_global, 
            _) = metrics

            # Seleziona precision, recall e F1 in base al tipo di metrica specificato
            if metric_type == "keyword extraction":
                precision = entity_precision
                recall = entity_recall
                f1_score = entity_f1_score
            elif metric_type == "keyword linking":
                precision = linking_precision_global
                recall = linking_recall_global
                f1_score = linking_f1_score_global
            else:
                raise ValueError(f"Tipo di metrica '{metric_type}' non riconosciuto. Usa 'entity extraction', 'global linking', o 'filtered linking'.")

            metrics_list.append((dirpath, precision, recall, f1_score))

        except Exception as e:
            print(f"Errore durante il calcolo delle metriche per la cartella {dirpath}: {e}")

    # Ordina le cartelle per F1 score in ordine decrescente
    metrics_list.sort(key=lambda x: x[3], reverse=True)  # x[3] è l'F1 score
    return metrics_list




# parameters (change the root_folder for evaluating the other approaches)
metric_type = "keyword linking"
gold_folder = "gold_standard"
root_folder = "Evaluation/baseline/"


# call function for evaluation
sorted_metrics = sort_metrics(root_folder, gold_folder, metric_type)

# Print results
print(f"\nResults order by F1 Score ({metric_type}):")
print("Model | Precision | Recall | F1 Score")
print("-" * 50)
for folder, precision, recall, f1_score in sorted_metrics:
    print(f"{folder} | {precision:.4f} | {recall:.4f} | {f1_score:.4f}")