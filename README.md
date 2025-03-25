This repository contains all the necessary files for an experiment to retrieve keywords using smaller open-source LLMs within narrative events and link them to Wikidata. We created a gold-standard dataset of textual narratives, structured into events, and manually annotated with keyword mentions and their corresponding Wikidata unique identifiers (QIDs). Wikidata serves as our reference knowledge base for this task.

We tested three approaches:

(1) Direct Linking: We prompted the selected LLMs to identify keywords in the text and directly link them to Wikidata QIDs. 
(2) SPARQL Querying: The LLMs identified keyword mentions, and we used the Wikidata SPARQL Endpoint to retrieve their QIDs. 
(3) Wikipedia-Based Linking: The LLMs identified keyword mentions and their corresponding Wikipedia titles, and we used Wikipedia APIs to obtain their Wikidata QIDs from the Wikipedia titles.

For all approaches, we measured precision, recall, and F1 score by comparing the model's predictions to our gold-standard annotations:

True Positive (TP): The model correctly identifies and links keywords to the correct Wikidata QIDs. 
False Positive (FP): The model predicts incorrect keywords or links them to the wrong QIDs. 
False Negative (FN): The model fails to identify the keywords present in the gold standard.
