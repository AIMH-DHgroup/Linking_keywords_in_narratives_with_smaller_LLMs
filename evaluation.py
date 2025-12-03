import os
import json
import matplotlib.pyplot as plt
import pandas as pd

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
    Calculate precision, recall e F1 score for keyword linking.
    """

    
# Metriche globali per l'keyword linking
    linking_true_positive_global = 0
    linking_false_positive_global = 0
    linking_false_negative_global = 0

    true_positives_per_file = {}
    false_positive_per_file = {}
    false_negative_per_file = {}

    for filename, gold_content in gold_data.items():
        predicted_content = predicted_data.get(filename.replace(".json", ".csv.json"))
        if not predicted_content:
            continue

        file_true_positive = []
        file_false_positive = []
        file_false_negative = []

        for gold_entities, pred_entities in zip(gold_content, predicted_content):
            gold_labels = [(entity["Wikipedia_label"], extract_wikidata_id(entity["Wikidata_ID"], nullTP)) for entity in gold_entities["keywords"]]
            pred_entities_processed = [
                (entity["originalKey"], entity["Wikidata_ID"]) for entity in pred_entities["keywords"]
            ]

            matched_gold = set()
            matched_pred = set()
            
            # TP 
            for i, (gold_label, gold_wikidata_id) in enumerate(gold_labels):
                for j, (pred_key, pred_wikidata_id) in enumerate(pred_entities_processed):
                
          
         
                    if jaccard_similarity(gold_label, pred_key) >= jaccard_threshold:
                        matched_gold.add(i)
                        matched_pred.add(j)
 


                       
                        if gold_wikidata_id == pred_wikidata_id:
                            linking_true_positive_global += 1
                            file_true_positive.append({
                                "gold_label": gold_label,
                                "pred_key": pred_key,
                                "gold_wikidata_id": gold_wikidata_id,
                                "pred_wikidata_id": pred_wikidata_id
                            })




                     
            #FP

            for pred_key, pred_wikidata_id in pred_entities_processed:
                isSimilar = False
                for gold_label, gold_wikidata_id in gold_labels:
                    if jaccard_similarity(gold_label, pred_key) >= jaccard_threshold:
                        isSimilar = True
                        # Se la stringa è simile ma l'ID non coincide → FP (linking errato)
                        if gold_wikidata_id != pred_wikidata_id:
                            linking_false_positive_global += 1
                            file_false_positive.append({
                                "gold_label": gold_label,
                                "pred_key": pred_key + " (id wrong)",
                                "gold_wikidata_id": gold_wikidata_id,
                                "pred_wikidata_id": pred_wikidata_id
                            })


                # Se nessuna stringa gold è simile → FP (entità inesistente)
                if not isSimilar:
                    linking_false_positive_global += 1
                    file_false_positive.append({
                        "gold_label": "",
                        "pred_key": pred_key + " (string not present in gold)",
                        "gold_wikidata_id": "",
                        "pred_wikidata_id": pred_wikidata_id
                    })
                        



                            

            #FN
            for i, (gold_label, gold_wikidata_id) in enumerate(gold_labels):
                best_match = None
                for j, (pred_key, pred_wikidata_id) in enumerate(pred_entities_processed):
                    if jaccard_similarity(gold_label, pred_key) >= jaccard_threshold:
                        best_match = pred_wikidata_id

                if best_match is None:
                    # mention gold non trovata
                    linking_false_negative_global += 1
                    file_false_negative.append({
                        "gold_label": gold_label +" (Mention Not found)",
                        "gold_wikidata_id": gold_wikidata_id
                    })
                elif best_match != gold_wikidata_id:
                    # mention trovata ma ID errato
                    linking_false_negative_global += 1
                    file_false_negative.append({
                        "gold_label": gold_label,
                        "gold_wikidata_id": gold_wikidata_id + " (Mention found with different id)"
                    })


        true_positives_per_file[filename] =  file_true_positive
        false_positive_per_file[filename] = file_false_positive
        false_negative_per_file[filename] =  file_false_negative
        
        

    # Metrichs for keyword linking
    linking_precision_global = linking_true_positive_global / (linking_true_positive_global + linking_false_positive_global) if (linking_true_positive_global + linking_false_positive_global) > 0 else 0
    linking_recall_global = linking_true_positive_global / (linking_true_positive_global + linking_false_negative_global) if (linking_true_positive_global + linking_false_negative_global) > 0 else 0
    linking_f1_score_global = (2 * linking_precision_global * linking_recall_global) / (linking_precision_global + linking_recall_global) if (linking_precision_global + linking_recall_global) > 0 else 0
                
                
    return (linking_precision_global, linking_recall_global, linking_f1_score_global, 
            true_positives_per_file, false_positive_per_file, false_negative_per_file)


def process_folders_recursively(gold_folder, root_folder, jaccard_threshold, stampaTP=False, stampaFP=False, stampaFN=False):
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
            (linking_precision_global, linking_recall_global, linking_f1_score_global, 
             true_positives_per_file, false_positives_per_file, false_negatives_per_file) = metrics

            # Stampa i risultati

            print(f"\nEntity Linking (Globale) - Precision: {linking_precision_global:.4f}")
            print(f"Entity Linking (Globale) - Recall: {linking_recall_global:.4f}")
            print(f"Entity Linking (Globale) - F1 Score: {linking_f1_score_global:.4f}")


            if stampaTP:
                print("\nTrue Positives per keyword Linking:")
                for filename, true_positives in true_positives_per_file.items():
                    print(f"\nFile: {filename}")
                    for tp in true_positives:
                        print(f"  Gold Label: {tp['gold_label']} | Predicted Key: {tp['pred_key']}")
                        print(f"    Gold Wikidata ID: {tp['gold_wikidata_id']} | Predicted Wikidata ID: {tp['pred_wikidata_id']}")
                        
            elif stampaFP:
                print("\nFalse Positive per keyword Linking:")
                for filename, false_positives in false_positives_per_file.items():
                    print(f"\nFile: {filename}")
                    for fp in false_positives:
                        print(f"  Gold Label: {fp['gold_label']} | Predicted Key: {fp['pred_key']}")
                        print(f"    Gold Wikidata ID: {fp['gold_wikidata_id']} | Predicted Wikidata ID: {fp['pred_wikidata_id']}")
                        
            elif stampaFN:
                print("\nFalse Negative per keyword Linking:")
                for filename, false_negatives in false_negatives_per_file.items():
                    print(f"\nFile: {filename}")
                    for fn in false_negatives:
                        print(f"  Gold Label: {fn['gold_label']} | Gold id: {fn['gold_wikidata_id']}")
          

        except Exception as e:
            #print(f"Errore durante il calcolo delle metriche per la cartella {dirpath}: {e}")
            a=9


def sort_metrics(root_folder, gold_folder, metric_type, t):
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
            metrics = calculate_metrics(gold_data, predicted_data, t)
            (linking_precision_global, linking_recall_global, linking_f1_score_global, 
            _, _, _) = metrics

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


def plot_all_metrics_trend(gold_folder, root_folder):
    """
    Mostra tre grafici (Precision, Recall, F1 score) per ogni modello,
    al variare della soglia di Jaccard.
    """
    # Carica i dati gold
    gold_data = load_json_files(gold_folder)
    thresholds = [round(x * 0.1, 1) for x in range(10, 0, -1)]

    # Prepara 3 subplot in un'unica figura
    fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=False)
    metrics = ["Precision", "Recall", "F1"]
    colors = ["tab:blue", "tab:orange", "tab:green"]  # opzionale, per coerenza visiva

    # Scorri tutte le sottocartelle del root_folder
    for model_name in sorted(os.listdir(root_folder)):
        model_path = os.path.join(root_folder, model_name)
        if not os.path.isdir(model_path):
            continue

        predicted_data = load_json_files(model_path)
        if not predicted_data:
            continue

        precision_values, recall_values, f1_values = [], [], []

        for t in thresholds:
            # Supponendo che calculate_metrics ritorni:
            # (TP, FP, FN, precision, recall, f1, altro)
            precision, recall, f1, _, _,_ = calculate_metrics(gold_data, predicted_data, t)

            precision_values.append(precision)
            recall_values.append(recall)
            f1_values.append(f1)

        # Disegna le curve su ciascun subplot
        axes[0].plot(thresholds, precision_values, marker='o', label=model_name)
        axes[1].plot(thresholds, recall_values, marker='o', label=model_name)
        axes[2].plot(thresholds, f1_values, marker='o', label=model_name)

    # Personalizzazione dei subplot
    for ax, metric, color in zip(axes, metrics, colors):
        ax.set_xlabel("Jaccard threshold", fontsize=12)
        ax.set_ylabel(f"{metric} score", fontsize=12)
        ax.set_title(f"{metric} trend", fontsize=13)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.set_xticks(thresholds)
        ax.legend(title="Models", fontsize=9)

    plt.tight_layout()
    plt.show()
    
def best_f1_per_model(gold_folder, root_folder, metric_type="keyword linking"):
    """
    Per ogni modello in root_folder:
    - calcola precision, recall, f1 per soglie da 1.0 a 0.1
    - seleziona la soglia con miglior f1
    - restituisce tabella ordinata per f1
    metric_type: 'keyword extraction' oppure 'keyword linking'
    """

    gold_data = load_json_files(gold_folder)
    thresholds = [round(x * 0.1, 1) for x in range(10, 0, -1)]
    results = []

    for model_name in sorted(os.listdir(root_folder)):
        model_path = os.path.join(root_folder, model_name)
        if not os.path.isdir(model_path):
            continue

        predicted_data = load_json_files(model_path)
        if not predicted_data:
            continue

        best_f1 = 0
        best_metrics = None
        best_threshold = None

        for t in thresholds:
            (link_precision, link_recall, link_f1,
             _, _, _) = calculate_metrics(gold_data, predicted_data, t)


            if metric_type == "keyword linking":
                precision, recall, f1 = link_precision, link_recall, link_f1
            else:
                raise ValueError("metric_type deve essere 'keyword extraction' o 'keyword linking'.")

            if f1 > best_f1:
                best_f1 = f1
                best_metrics = (precision, recall, f1)
                best_threshold = t

        if best_metrics:
            results.append({
                "LLM": model_name,
                "Precision": best_metrics[0],
                "Recall": best_metrics[1],
                "F1": best_metrics[2],
                "Threshold": best_threshold
            })

    # Crea tabella ordinata per F1
    if results:
        df = pd.DataFrame(results).sort_values(by="F1", ascending=False).reset_index(drop=True)
        print("\nTabella dei migliori modelli (ordinata per F1):")
        print(df.to_string(index=False))
        return df
    else:
        print("⚠️ Nessun modello valido trovato.")
        return pd.DataFrame(columns=["Modello", "Precision", "Recall", "F1", "Soglia"])


def fp_percentages_per_model(gold_folder, root_folder, jaccard_threshold, nullTP=False):
    """
    Calcola, per ogni modello (sottocartella di root_folder), le percentuali di
    False Positive dovuti a:
      - id errato (pred_key contiene ' (id wrong)')
      - stringa non presente nel gold (pred_key contiene ' (string not present in gold)')

    Usa la funzione calculate_metrics esistente, senza modificarne la logica.
    Ritorna un DataFrame con una riga per modello e disegna un grafico a torta
    per ciascun modello.
    """

    # Carico una sola volta il gold
    gold_data = load_json_files(gold_folder)
    if not gold_data:
        print("Nessun file gold valido trovato.")
        return pd.DataFrame()

    results = []

    # Ogni sottocartella di root_folder è un modello
    for model_name in sorted(os.listdir(root_folder)):
        model_path = os.path.join(root_folder, model_name)
        if not os.path.isdir(model_path):
            continue

        predicted_data = load_json_files(model_path)
        if not predicted_data:
            print(f"Modello '{model_name}': nessun file JSON di predizione trovato, salto.")
            continue

        try:
            # Riutilizzo ESATTAMENTE la tua funzione
            (_prec, _rec, _f1,
             _tp_per_file,
             false_positive_per_file,
             _fn_per_file) = calculate_metrics(gold_data, predicted_data, jaccard_threshold, nullTP=nullTP)
        except Exception as e:
            print(f"Errore nel modello '{model_name}': {e}")
            continue

        total_fp = 0
        fp_id_wrong = 0
        fp_string_not_in_gold = 0

        # Scorro tutti gli FP prodotti da calculate_metrics
        for filename, fps in false_positive_per_file.items():
            for fp in fps:
                total_fp += 1
                pred_key = fp.get("pred_key", "")

                if "(id wrong)" in pred_key:
                    fp_id_wrong += 1
                elif "(string not present in gold)" in pred_key:
                    fp_string_not_in_gold += 1
                # eventualmente qui potresti distinguere altri tipi di FP in futuro

        # Calcolo percentuali (se non ci sono FP → 0)
        if total_fp > 0:
            fp_id_ratio = fp_id_wrong / total_fp
            fp_string_ratio = fp_string_not_in_gold / total_fp
        else:
            fp_id_ratio = 0.0
            fp_string_ratio = 0.0

        # Salvo nei risultati tabellari
        results.append({
            "Model": model_name,
            "FP_total": total_fp,
            "FP_id_wrong_ratio": fp_id_ratio,
            "FP_string_not_in_gold_ratio": fp_string_ratio
        })

        # -------------------------------
        # GRAFICO A TORTA PER QUESTO MODELLO
        # -------------------------------
        if total_fp > 0:
            other_fp = total_fp - fp_id_wrong - fp_string_not_in_gold

            labels = []
            sizes = []

            if fp_id_wrong > 0:
                labels.append("Wrong QID")
                sizes.append(fp_id_wrong)
            if fp_string_not_in_gold > 0:
                labels.append("Wrong keywords")
                sizes.append(fp_string_not_in_gold)
            if other_fp > 0:
                labels.append("Altri FP")
                sizes.append(other_fp)

            # Disegno il pie chart
            fig, ax = plt.subplots()
            ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # per farla rotonda
            ax.set_title(f"{model_name}")
            plt.show()
        else:
            print(f"'{model_name}': nessun FP, nessun grafico a torta.")

    if not results:
        print("Nessun modello valido trovato.")
        return pd.DataFrame(columns=["Model", "FP_total", "FP_id_wrong_ratio", "FP_string_not_in_gold_ratio"])

    df = pd.DataFrame(results).sort_values(by="Model").reset_index(drop=True)

    print("\nPercentuali di False Positive per modello:")
    print(df.to_string(index=False))

    return df



# parameters (change the root_folder for evaluating the other approaches)
metric_type = "keyword linking"
gold_folder = "gold_standard/"

root_folder = "Evaluation/third_approach/"

jaccard = 1


    
# print keywords for a jaccard threshold    
#process_folders_recursively(gold_folder, root_folder, jaccard, stampaFN=True)


#Print precision, recall and f1 of 1 approach
sorted_metrics = sort_metrics(root_folder, gold_folder, metric_type, jaccard)
print(f"\nResults order by F1 Score ({metric_type}):")
print("Model | Precision | Recall | F1 Score")
print("-" * 50)
for folder, precision, recall, f1_score in sorted_metrics:
    print(f"{folder} | {precision:.4f} | {recall:.4f} | {f1_score:.4f}")


# print results of the best jcaccard threshold  
df_results = best_f1_per_model(
    gold_folder=gold_folder,
    root_folder=root_folder,
    metric_type="keyword linking"   
)

# # print plot of f1, precision and recall for each jaccard threshold 
#plot_all_metrics_trend(gold_folder, root_folder)



#f_fp = fp_percentages_per_model(gold_folder, root_folder, jaccard)
    
