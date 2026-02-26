import java.io.*;


import java.util.*;

import java.io.File;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Set;
import java.util.Vector;

public class InvokeNLPHub {

	static String dataMinerURL = "dataminer-prototypes.cloud.d4science.org";
	static String token = "INSERT-YOUR-TOKEN-HERE"; //statistical.manager
	public LinkedHashMap<String,Set<String>> allEntities = new LinkedHashMap<>();
	public LinkedHashMap<String,Set<String>> potentialGeospatialEntities = new LinkedHashMap<>();
	public Vector<String> entitiesAll = new Vector<>();
	public Vector<String> keywordsAll = new Vector<>();
	public Vector<String> v3 = new Vector<>();
	
	public String getEntities(List<String> entities,File inputFileUTF8, String language) throws Exception {
		
		
		List<String> annotations = null;
		annotations = entities;
		
		/*
		String allAnnotations = NLPHubCaller.loadString("Annotations_example.txt", "UTF-8");
		String alllogs = "";
		*/
				
		NLPHubCaller caller = new NLPHubCaller(dataMinerURL, token);
		caller.run(language, inputFileUTF8, annotations);

		System.out.println("JSON output is in: " + caller.getOutputJsonFile());
		System.out.println("Annotated text is in: " + caller.getOutputAnnotationFile());
		// example of output
		
		
		String allAnnotations = NLPHubCaller.loadString(caller.getOutputAnnotationFile().getAbsolutePath(), "UTF-8");
		String alllogs = NLPHubCaller.loadString(caller.getLogFile().getAbsolutePath(), "UTF-8");
		
		
		
		
		String allAnnotationsNotExtracted = allAnnotations.replace("##", "");
		
		int nAnn = ((allAnnotations.length() - allAnnotationsNotExtracted.length()) / 4) - 1;
		
		

		System.out.println(allAnnotations);
		String splitAnnotations[] = allAnnotations.split("\n");
		boolean collecting = false;
		for (String a:splitAnnotations) {
			a = a.trim();
			if (a.equals("##MERGED##")) {
				
				collecting = true;
				
			}else if ( (a.length()==0 || a.startsWith("##")) && collecting) {
				collecting = false;
			}else if (a.startsWith("#") && collecting) {
				int column = a.indexOf(":");
				String ne = a.substring(0,column);
				ne = ne.replace("#", "").trim();
				String sentence = a.substring(column+1);
				Set<String> extrentities = extractEntities(sentence); 
				System.out.println("Named entity: "+ne+" -> "+extrentities);
				allEntities.put(ne, extrentities);
				
				if(!ne.equals("Keyword")) {

				    for (String elemento : extrentities) {
				      entitiesAll.add(elemento);
				    }
				
				} else {
					
				    for (String elemento : extrentities) {
					   keywordsAll.add(elemento);
					}	
				    
				}
				
				if (ne.equalsIgnoreCase("Location") || ne.equalsIgnoreCase("Keyword"))
					potentialGeospatialEntities.put(ne, extrentities);
			}
			
		}
		
		
		System.out.println("N of algorithms that extracted information " + nAnn);

		caller.outputAnnotationFile.delete();
		caller.outputJsonFile.delete();
		caller.outputLogFile.delete();
		
		if (alllogs.contains("Unparsable"))
			throw new Exception("Something went wrong");
		

		System.out.println("##########");
		entitiesAll.add("DAQUISEPARATOREKEYWORDS");
		
		v3.addAll (entitiesAll);
		v3.addAll (keywordsAll);
		
		String a = String.join(", ", v3);
		System.out.println(a);
		return a;

	}
	
	public static Set<String> extractEntities(String annotatedString){
		Set<String> entities = new LinkedHashSet();
		
		int idx = annotatedString.indexOf("[");
		while (idx>-1) {
			int idxclose = annotatedString.indexOf("]");
			if (idxclose<0)
				break;
			String en = annotatedString.substring(idx+1,idxclose);
			en = en.trim();
			entities.add(en);
			annotatedString = annotatedString.substring(idxclose+1);
			idx = annotatedString.indexOf("[");
		}
		
		return entities;
		
	}

	
	
    public static void main(String[] args) throws Exception {
        // Specifica il percorso della cartella contenente i file CSV
        String folderPath = "csv";

        // Configurazione per NLP
        List<String> entities = new ArrayList<>();
        entities.add("Location");
        entities.add("Person");
        entities.add("Organization");
        entities.add("Keyword");

        String language = "en";

        // Chiama il metodo per processare i file CSV e eseguire NLP
        processCsvFilesAndRunNlp(folderPath, entities, language);
    }

    /**
     * Legge tutti i file CSV nella cartella, estrae la seconda colonna (saltando la prima riga),
     * elabora il contenuto con NLP e scrive i risultati in un nuovo file CSV nella cartella "output".
     *
     * @param folderPath  Percorso della cartella con i file CSV.
     * @param entities    Entità da rilevare.
     * @param language    Lingua da utilizzare.
     */
    private static void processCsvFilesAndRunNlp(String folderPath, List<String> entities, String language) throws IOException {
        File folder = new File(folderPath);
        File[] files = folder.listFiles((dir, name) -> name.toLowerCase().endsWith(".csv"));

        if (files == null || files.length == 0) {
            System.out.println("Nessun file CSV trovato nella cartella specificata.");
            return;
        }

        // Crea la cartella "output" se non esiste
        File outputFolder = new File("output");
        if (!outputFolder.exists() && !outputFolder.mkdirs()) {
            System.err.println("Impossibile creare la cartella output.");
            return;
        }

        for (File file : files) {
            System.out.println("Processing file: " + file.getName());
            File outputFile = new File(outputFolder, file.getName());

            try (BufferedReader reader = new BufferedReader(new FileReader(file));
            	     BufferedWriter writer = new BufferedWriter(new FileWriter(outputFile, true))) {

            	    String line;
            	    boolean isFirstLine = true;

            	    while ((line = reader.readLine()) != null) {
            	        if (isFirstLine) {
            	            isFirstLine = false; // Salta la prima riga (intestazione)
            	            continue;
            	        }

            	        String content = extractSecondColumn(line);
            	        if (content != null) { // Elabora solo se esiste la seconda colonna
            	            // Scrivi il contenuto nel file temporaneo
            	            String tempFileName = "sampleTextBBC.txt";
            	            try (BufferedWriter tempWriter = new BufferedWriter(new FileWriter(tempFileName))) {
            	                tempWriter.write(content);
            	                tempWriter.newLine();
            	            }

            	            // Chiama la funzione NLP
            	            File input = new File(tempFileName);
            	            InvokeNLPHub nlp = new InvokeNLPHub();
            	            String nlpResult;
            	            try {
            	                nlpResult = nlp.getEntities(entities, input, language);
            	                System.out.println("RESULT for line: " + content + " -> " + nlpResult);
            	            } catch (Exception e) {
            	                System.err.println("Errore nell'elaborazione NLP per la riga: " + content);
            	                e.printStackTrace();
            	                nlpResult = "ERROR";
            	            }

            	            // Elimina il file temporaneo dopo l'elaborazione
            	            if (!input.delete()) {
            	                System.err.println("Impossibile eliminare il file temporaneo: " + tempFileName);
            	            }

            	            // Scrivi il risultato nel file di output, racchiuso in doppi apici
            	            writer.write("\"" + nlpResult.replace("\"", "\"\"") + "\"");
            	            writer.newLine();
            	        }
            	    }
            	} catch (IOException e) {
            	    System.err.println("Errore nella lettura del file: " + file.getName());
            	    e.printStackTrace();
            	}
        }
    }

    /**
     * Estrae il contenuto della seconda colonna da una riga di un CSV utilizzando "," o "|" come separatori,
     * rispettando i delimitatori di testo (").
     *
     * @param line  Riga del file CSV.
     * @return      Contenuto della seconda colonna, oppure null se non esiste.
     */
    private static String extractSecondColumn(String line) {
        // Usando un'espressione regolare per gestire i delimitatori e i separatori
        final String regex = ",(?=([^\"]*\"[^\"]*\")*[^\"]*$)|\\|(?=([^\"]*\"[^\"]*\")*[^\"]*$)";
        String[] columns = line.split(regex, -1);

        if (columns.length > 1) {
            // Rimuovi i doppi apici, se presenti
            return columns[1].replaceAll("^\"|\"$", "").trim();
        }
        return null;
    }
	
	
}
