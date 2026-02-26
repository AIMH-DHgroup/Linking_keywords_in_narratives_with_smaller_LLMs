import java.io.BufferedReader;

import java.io.BufferedWriter;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.io.OutputStreamWriter;
import java.io.Reader;
import java.io.StringWriter;
import java.io.UnsupportedEncodingException;
import java.io.Writer;
import java.net.HttpURLConnection;
import java.net.ProtocolException;
import java.net.URL;
import java.net.URLConnection;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.List;
import java.util.UUID;

import javax.xml.parsers.DocumentBuilder;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.transform.OutputKeys;
import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.dom.DOMSource;
import javax.xml.transform.stream.StreamResult;

import org.w3c.dom.Document;

public class NLPHubCaller {

	static String dataMinerProcessUrl = "https://#DM#/wps/WebProcessingService?request=Execute&service=WPS&Version=1.0.0";
	public String dataMinerUrl = "";
	public String token = "";
	public int refreshTime = 10000;
	public File outputJsonFile;
	public File outputAnnotationFile;
	public File outputLogFile;

	public File getOutputJsonFile() {
		return outputJsonFile;
	}

	public File getOutputAnnotationFile() {
		return outputAnnotationFile;
	}

	public File getLogFile() {
		return outputLogFile;
	}

	public NLPHubCaller(String dataMinerURL, String token) {
		this.dataMinerUrl = dataMinerURL;
		this.token = token;
	}

	public NLPHubCaller() {
		this.dataMinerUrl = "dataminer-prototypes.d4science.org"; // url of
		// the DM in
		// the
		// RPrototypingLab
		// VRE
		this.token = "fea75a5a-d84c-495f-b0ca-09cdd95bacce-843339462"; // Token
		// of
		// the
		// RPrototypingLab
		// VRE
	}

	private static void pipe(Reader reader, Writer writer) throws IOException {
		char[] buf = new char[1024];
		int read = 0;
		while ((read = reader.read(buf)) >= 0) {
			writer.write(buf, 0, read);
		}
		writer.flush();
	}

	public static void postData(Reader data, URL endpoint, Writer output) throws Exception {
		HttpURLConnection urlc = null;
		try {
			urlc = (HttpURLConnection) endpoint.openConnection();
			try {
				urlc.setRequestMethod("POST");
			} catch (ProtocolException e) {
				throw new Exception("Shouldn't happen: HttpURLConnection doesn't support POST??", e);
			}
			urlc.setDoOutput(true);
			urlc.setDoInput(true);
			urlc.setUseCaches(false);
			urlc.setAllowUserInteraction(false);
			urlc.setRequestProperty("Content-type", "text/xml; charset=" + "UTF-8");

			OutputStream out = urlc.getOutputStream();

			try {
				Writer writer = new OutputStreamWriter(out, "UTF-8");
				pipe(data, writer);
				writer.close();
			} catch (IOException e) {
				throw new Exception("IOException while posting data", e);
			} finally {
				if (out != null)
					out.close();
			}

			InputStream in = urlc.getInputStream();
			try {
				Reader reader = new InputStreamReader(in);
				pipe(reader, output);
				reader.close();
			} catch (IOException e) {
				throw new Exception("IOException while reading response", e);
			} finally {
				if (in != null)
					in.close();
			}

		} catch (IOException e) {
			throw new Exception("Connection error (is server running at " + endpoint + " ?): " + e);
		} finally {
			if (urlc != null)
				urlc.disconnect();
		}
	}

	public static String getStatus(String endpoint) {
		String result = null;

		// Send a GET request to the servlet
		try {
			// Send data
			String urlStr = endpoint;

			URL url = new URL(urlStr);
			URLConnection conn = url.openConnection();
			conn.setConnectTimeout(120000);
			conn.setReadTimeout(120000);

			// Get the response
			BufferedReader rd = new BufferedReader(new InputStreamReader(conn.getInputStream()));
			StringBuffer sb = new StringBuffer();
			String line;
			while ((line = rd.readLine()) != null) {
				sb.append(line);
			}
			rd.close();
			result = sb.toString();
		} catch (Exception e) {
			e.printStackTrace();
		}

		return result;
	}

	public void run(String language, File textFile, List<String> annotations) throws Exception {
		System.out.println("NLPHUB client has started");
		File template = null;
		String annotationsList = "";

		template = new File("NLPHubTemplate.txt");
		annotationsList = annotations.toString().replace("[", "").replace("]", "").replace(",", "|").replaceAll(" +", "");
		System.out.println("Annotation List requested: " + annotationsList);
		byte[] encoded = Files.readAllBytes(Paths.get(template.getPath()));
		String content = new String(encoded, "UTF-8");
		System.out.println("Preprocessing text");
		String text = preprocess(textFile);

		content = content.replace("#LANGUAGE#", language);
		content = content.replace("#CONTENT#", text);
		content = content.replace("#ANNOTATIONS#", annotationsList);

		File tempFile = new File("NLPHUB_" + UUID.randomUUID() + ".txt");
		FileWriter fw = new FileWriter(tempFile);
		fw.write(content);
		fw.close();

		StringWriter sw = new StringWriter();
		FileReader fr = new FileReader(tempFile);

		System.out.println("Running...");
		long t0 = System.currentTimeMillis();
		postData(fr, new URL(dataMinerProcessUrl.replace("#DM#", dataMinerUrl) + "&gcube-token=" + token), sw);

		fr.close();

		String answer = sw.toString();

		String statusLocation = answer.substring(answer.indexOf("statusLocation=\"") + "statusLocation=\"".length(), answer.indexOf("\">"));

		// System.out.println(sw.toString());
		// System.out.println(statusLocation);

		String status = getStatus(statusLocation + "&gcube-token=" + token);

		while (!(status.contains("wps:ProcessSucceeded") || status.contains("wps:ProcessFailed"))) {
			System.out.println(status);
			status = getStatus(statusLocation + "&gcube-token=" + token);
			Thread.sleep(refreshTime);
		}
		long t1 = System.currentTimeMillis();

		System.out.println("Finished in " + (t1 - t0) + " ms");

		// System.out.println(status);
		// tempFile.delete();

		if (status.contains("wps:ProcessFailed")) {
			System.out.println("Process Failed!");
			throw new Exception("Process failed");
		} else {

			String UrlToLog = status.substring(status.indexOf("<d4science:Data>") + "<d4science:Data>".length(), status.indexOf("</d4science:Data>"));
			System.out.println("NLPHub - Url to Log:" + UrlToLog);
			outputLogFile = new File("Log_" + UUID.randomUUID() + ".txt");
			downloadFile(UrlToLog, outputLogFile.getAbsolutePath());

			status = status.substring(status.indexOf("</d4science:Data>") + "</d4science:Data>".length() + 1);
			String UrlToJSON = status.substring(status.indexOf("<d4science:Data>") + "<d4science:Data>".length(), status.indexOf("</d4science:Data>"));
			System.out.println("NLPHub - Url to json output:" + UrlToJSON);
			outputJsonFile = new File("Output_" + UUID.randomUUID() + ".json");
			downloadFile(UrlToJSON, outputJsonFile.getAbsolutePath());

			status = status.substring(status.indexOf("</d4science:Data>") + "</d4science:Data>".length() + 1);
			String UrlToAnnotation = status.substring(status.lastIndexOf("<d4science:Data>") + "<d4science:Data>".length(), status.lastIndexOf("</d4science:Data>"));
			System.out.println("NLPHub - Url to annotation:" + UrlToAnnotation);
			outputAnnotationFile = new File("Annotations_" + UUID.randomUUID() + ".txt");
			downloadFile(UrlToAnnotation, outputAnnotationFile.getAbsolutePath());
			tempFile.delete();

		}
	}

	public static void downloadFile(String fileurl, String localFile) throws Exception {
		URL smpFile = new URL(fileurl);
		URLConnection uc = (URLConnection) smpFile.openConnection();
		InputStream is = uc.getInputStream();
		inputStreamToFile(is, localFile);
		is.close();
		is = null;
		System.gc();
	}

	public static void inputStreamToFile(InputStream is, String path) throws FileNotFoundException, IOException {
		FileOutputStream out = new FileOutputStream(new File(path));
		byte buf[] = new byte[1024];
		int len = 0;
		while ((len = is.read(buf)) > 0)
			out.write(buf, 0, len);
		out.close();
	}

	public static String preprocess(File textFile) throws Exception {
		try {
			byte[] encoded = Files.readAllBytes(Paths.get(textFile.getPath()));
			String content = new String(encoded, "UTF-8");
			content = cleanCharacters(content);
			content = content.replace("'", "");
			return content;
		} catch (Exception e) {
			System.out.println("Eror while reading file " + e.getMessage());
			throw e;
		}
	}
	
	
	static char[] charsToSave = {'Ă','ă','ć','Ό','Č','č','А','Α','Δ','Ε','Η','ș','Ț','ț','Μ','Ν','Ο','ğ','Ρ','Τ','Υ','€','ά','έ','ή','ί','İ','α','ı','β','γ','δ','ε','η','ι','κ','λ','μ','ν','Ľ','ľ','ο','π','ρ','Á','ς','Â','σ','τ','υ','χ','Ç','ň','ω','ό','ύ','Î','Ş','ß','ş','Š','š','ţ','ű','Ž','ž'};
	public static String cleanCharacters(String source) {

		char c = 0;
		for (int i = 0; i < source.length(); i++) {
			c = source.charAt(i);
			if (!((c >= 33 && c <= 90) || (c >= 97 && c <= 122) || (c >= 128 && c <= 167) || (c >= 180 && c <= 183) || (c >= 210 && c <= 212) || (c >= 214 && c <= 216) || (c >= 224 && c <= 255))) {
				boolean tosave = false;
				for (char cts:charsToSave) {
					if (c==cts)
					{tosave = true;
					break;}
				}
				if (!tosave)
					source = source.replace(source.substring(i, i + 1), " ");
			} else if (c == '&') {
				source = source.replace(source.substring(i, i + 1), "and");
			}
		}

		source = source.replaceAll("[\\s]+", " ").trim();
		source = source.replaceAll("<", " ").trim();
		source = source.replaceAll(">", " ").trim();
		return source;
	}
	
	public static String compressStrangeCharacters(String source) {

		char c = 0;
		for (int i = 0; i < source.length(); i++) {
			c = source.charAt(i);
			if (!((c >= 33 && c <= 90) || (c >= 97 && c <= 122) || (c >= 128 && c <= 167) || (c >= 180 && c <= 183) || (c >= 210 && c <= 212) || (c >= 214 && c <= 216) || (c >= 224 && c <= 255))) {
				boolean tosave = false;
				for (char cts:charsToSave) {
					if (c==cts)
					{tosave = true;
					break;}
				}
				if (!tosave) {
					source = source.replace(source.substring(i, i + 1), " ");
				}else {
					if (source.toLowerCase().contains("capita income"))
						source = source.replace(source.substring(i, i + 1), " ");
					else
						source = source.replace(source.substring(i, i + 1), "");
				}
			} else if (c == '&') {
				source = source.replace(source.substring(i, i + 1), "and");
			}
		}

		source = source.replaceAll("[\\s]+", " ").trim();
		source = source.replaceAll("<", " ").trim();
		source = source.replaceAll(">", " ").trim();
		return source;
	}
	
	public static HashSet<Character> getStrangeCharacters(String source) {

		char c = 0;
		HashSet<Character> strange = new HashSet<>();
		
		for (int i = 0; i < source.length(); i++) {
			c = source.charAt(i);
			if (!((c >= 33 && c <= 90) || (c >= 97 && c <= 122) || (c >= 128 && c <= 167) || (c >= 180 && c <= 183) || (c >= 210 && c <= 212) || (c >= 214 && c <= 216) || (c >= 224 && c <= 255))) {
				boolean tosave = false;
				for (char cts:charsToSave) {
					if (c==cts)
					{tosave = true;
					break;}
				}
				if (!tosave)
					strange.add(c);
			} else if (c == '&') {
			}
		}

		return strange;
	}
	
	public static String readXMLDoc(String xmlFilePath) throws Exception {
		String xml = null;
		InputStream stream = null;
		try{
			try {
				File fl = new File(xmlFilePath);
				stream = new FileInputStream(fl);
			} catch (Exception e) {
				stream = ClassLoader.getSystemResourceAsStream(xmlFilePath);
			}
			DocumentBuilder dBuilder = DocumentBuilderFactory.newInstance()
					.newDocumentBuilder();

			Document doc = dBuilder.parse(stream);
			xml = toString(doc);
			return xml;
		}finally{
			if (stream!=null)
				stream.close();
		}
	}

	private static String toString(Document doc) {
		try {
			StringWriter sw = new StringWriter();
			TransformerFactory tf = TransformerFactory.newInstance();
			Transformer transformer = tf.newTransformer();
			transformer.setOutputProperty(OutputKeys.OMIT_XML_DECLARATION, "no");
			transformer.setOutputProperty(OutputKeys.METHOD, "xml");
			transformer.setOutputProperty(OutputKeys.INDENT, "yes");
			transformer.setOutputProperty(OutputKeys.ENCODING, "UTF-8");

			transformer.transform(new DOMSource(doc), new StreamResult(sw));
			return sw.toString();
		} catch (Exception ex) {
			throw new RuntimeException("Error converting to String", ex);
		}
	}

	public static void saveString2File(String filename, String string2save) throws Exception {

	}

	public static boolean checkInput(String filename) {
		File file = new File(filename);
		if (!file.exists())
			return false;
		if (!file.canRead())
			return false;
		else
			return true;
	}

	public static boolean checkOutput(String filename, boolean overwrite) {
		File file = new File(filename);
		if (!overwrite && file.exists())
			return false;
		if (file.exists() && (file.isDirectory() || !file.canWrite()))
			return false;
		else
			return true;		
	}

	public static String loadString(String filename, String encoding) throws Exception {
		try {
			if (checkInput(filename)) {

				BufferedReader in = new BufferedReader(new InputStreamReader(new FileInputStream(filename), encoding));
				String line = null;
				StringBuilder vud = new StringBuilder();

				while ((line = in.readLine()) != null) {
					vud.append(line + "\n");
				}
				in.close();
				return vud.toString();
			} else
				return null;
		} catch (UnsupportedEncodingException e) {
			e.printStackTrace();
			throw new Exception("The file " + filename + " is not in the correct format!");
		} catch (IOException e) {
			throw new Exception("The file " + filename + " is not in the correct format!");
		}
	}

	public static void saveString(String filename, String s, boolean overwrite, String encoding) throws Exception {
		try {
			if (checkOutput(filename, overwrite)) {
				Writer out = new BufferedWriter(new OutputStreamWriter(new FileOutputStream(filename), encoding));
				out.write(s);
				out.close();
			}
		} catch (IOException e) {
			throw new Exception("The system can not write in " + filename,e);
		}
	}
}
