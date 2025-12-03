This repository contains all the resources required for an experiment aimed at extracting keywords from textual descriptions using small open-source LLMs and linking them to Wikidata to populate a Knowledge Graph.

We selected a dataset from the CSV files collected within the MOuntain Valorisation through INterconnectedness and Green growth (MOVING) Horizon 2020 project. (https://www.moving-h2020.eu/)
Each CSV file contains a textual description of an european mountain value chain. Then, a gold
standard was created in which the keywords mentioned in the textual descriptions and
their corresponding Wikidata QIDs were manually annotated.

We tested three approaches:

(1) Direct Linking: We prompted the selected LLMs to identify keywords in the text and directly link them to Wikidata QIDs. 

(2) SPARQL Querying: The LLMs identified keyword mentions, and we used the Wikidata SPARQL Endpoint to retrieve their QIDs. 

(3) Wikipedia-Based Linking: The LLMs identified keyword mentions and their corresponding Wikipedia titles, and we used Wikipedia APIs to obtain their Wikidata QIDs from the Wikipedia titles.

For all approaches, we measured precision, recall, and F1 score by comparing the model's predictions to the gold-standard annotations:

True Positive (TP): The model correctly identifies entities where the mentions in
the text exactly match the annotated entities in the gold standard and links them
to the correct Wikidata QIDs, e.g. the entity ”Apuan Alps” matched with the entity
”Apuan Alps” in the gold standard, and linked with the Wikidata QID Q622309
(that corresponds to the Apuan Alps Wikidata entity)

False Positive (FP): The model predicts entities that either do not match the anno-
tated entities in the gold standard or are linked to incorrect Wikidata QIDs, e.g.
the entity ”Apuan Alps” that does not match with the entity ”Apuan Alps” in the
gold standard, or it match, but is linked with the Wikidata QID Q327434 (that
corresponds to the Austrian Alps Wikidata entity)

False Negative (FN): The model fails to identify entities annotated in the gold
standard, e.g., the entity ”mountain” (with Wikidata QID Q8502) that is present
in the gold standard but never identified by the model.
