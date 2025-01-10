import time
import google.generativeai as genai
import os
import pandas as pd
import base64
import requests
import time
from requests.exceptions import RequestException
from google.api_core.exceptions import ResourceExhausted
import io
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import PyPDF2
from dotenv import load_dotenv

load_dotenv()

class DocumentDTO:
    def __init__(self, link, numero_cnj, instancia, sistema, tribunal, tipo_documento, ha_liminar, tutela_antecipada, audiencia_designada, notificacao_extrajudicial, oficio, prazo_tutela_antecipada, tipo_audiencia, data_audiencia, hora_audiencia):
        self.link = link
        self.numero_cnj = numero_cnj
        self.instancia = instancia
        self.sistema = sistema
        self.tribunal = tribunal
        self.tipo_documento = tipo_documento
        self.ha_liminar = ha_liminar
        self.tutela_antecipada = tutela_antecipada
        self.audiencia_designada = audiencia_designada
        self.notificacao_extrajudicial = notificacao_extrajudicial
        self.oficio = oficio
        self.prazo_tutela_antecipada = prazo_tutela_antecipada
        self.tipo_audiencia = tipo_audiencia
        self.data_audiencia = data_audiencia
        self.hora_audiencia = hora_audiencia

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

csv_file_path = 'data.csv'
df = pd.read_csv(csv_file_path)
df.rename(columns={
    'Link dos Documentos': 'link',
    'Numero CNJ': 'numero_cnj',
    'Instância': 'instancia',
    'Sistema': 'sistema',
    'Tribunal': 'tribunal',
    'Tipo documento': 'tipo_documento',
    'Ha liminar': 'ha_liminar',
    'Tutela antecipada': 'tutela_antecipada',
    'Audiência designada': 'audiencia_designada',
    'Notificação extrajudicial': 'notificacao_extrajudicial',
    'Ofício': 'oficio',
    'Prazo da tutela antecipada': 'prazo_tutela_antecipada',
    'Tipo de audiência': 'tipo_audiencia',
    'Data audiência': 'data_audiencia',
    'Hora audiência': 'hora_audiencia'
}, inplace=True)

doc_list = [DocumentDTO(**doc) for doc in df.to_dict(orient='records')]

model = genai.GenerativeModel('gemini-1.5-flash')

def convert_drive_link_to_download(url):
    if "drive.google.com" in url:
        file_id = url.split('/d/')[1].split('/')[0]
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return url


def extract_text_from_pdf(pdf_content):
    text = ""
    try:
        pdf_file = io.BytesIO(pdf_content)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        for page in pdf_reader.pages:
           text += page.extract_text()
    except Exception as e:
        print(f"Erro ao extrair texto do PDF com PyPDF2: {e}")
    return text

def extract_text_from_scanned_pdf(pdf_content):
    try:
        images = convert_from_bytes(pdf_content)
        text = ""
        for img in images:
            text += pytesseract.image_to_string(img, lang='por')
        return text
    except Exception as e:
        print(f"Erro ao extrair texto do PDF com OCR: {e}")
        return ""


def download_and_extract_text(url):
        try:
           download_url = convert_drive_link_to_download(url)
           response = requests.get(download_url, timeout=10)
           response.raise_for_status()
           pdf_content = response.content
           text = extract_text_from_pdf(pdf_content)
           if not text.strip():
               text = extract_text_from_scanned_pdf(pdf_content)
           return text
        except RequestException as e:
            print(f"Erro ao baixar ou processar o arquivo: {url} - {e}")
            return None


def create_prompt(examples, new_document):
    """Cria um prompt com exemplos e instruções para classificação."""

    prompt = """
    Instruções: Classifique o documento judicial abaixo em uma das seguintes categorias:
    - Carta de Intimação
    - Carta de Citação
    - Decisão
    - Carta de Notificação
    - Ofício à Operadora AMIL

    - **Carta de Intimação:** Se o documento tiver o objetivo principal de informar uma das partes sobre uma decisão proferida anteriormente, para que ela cumpra, faça ou deixe de fazer algo. O título geralmente indica "Mandado de Intimação" ou "Carta de Intimação" ou "Intimação" e o texto contém verbos como "intime-se", e a ordem para que a parte cumpra a decisão. O documento é uma ordem para que o oficial de justiça faça algo em relação a uma decisão proferida.
    - **Carta de Citação:** Se o documento notificar formalmente alguém para comparecer a um processo judicial como réu. O título geralmente indica "Carta de Citação" e o texto contém verbos como "cite-se" e a ordem para o réu comparecer ao processo.
    - **Decisão:** Se o documento apresentar uma resolução judicial, com análise do caso e um pronunciamento final sobre um pedido, ainda que de caráter liminar.  O título principal geralmente indica "Decisão" e o texto contém verbos como "decido", "defiro", ou "indefiro" e uma ordem judicial. Não confunda com uma ordem de cumprimento.
    - **Carta de Notificação:** Se o documento tiver o objetivo de notificar uma das partes sobre algo, mas não para comparecer a um processo diretamente (ex: uma decisão). O título geralmente indica "Carta de Notificação" e o texto contém verbos como "notifique-se".
    - **Ofício à Operadora AMIL:** Se o documento for explicitamente um ofício direcionado à operadora AMIL. O título geralmente indica "Ofício" e o documento é endereçado diretamente à AMIL.

    Exemplos:

    """
    for example in examples:
        prompt += f"""
        Documento: {example['text'][:100]}...
        Classificação: {example['label']}
        """

    prompt += f"""
    Documento a ser classificado:
    {new_document[:100]}...

    Classificação:
    """
    return prompt


def classify_document(examples, document_text, retry_count=3, delay=5):
    """Classifica um documento usando o modelo Gemini."""
    prompt = create_prompt(examples, document_text)
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except ResourceExhausted as e:
        if retry_count > 0:
            print(f"Limite atingido. Esperando {delay} segundos e tentando novamente... ({retry_count} tentativas restantes)")
            time.sleep(delay)
            return classify_document(examples, document_text, retry_count - 1, delay * 2) # aumenta o delay em dobro
        else:
            print(f"Erro: Limite de uso da API atingido após várias tentativas: {e}")
            return None


# Preparação dos Exemplos (In-context Learning)
num_examples = min(5, len(doc_list))  # Limita o número de exemplos
examples = []
for i in range(num_examples):
    text = download_and_extract_text(doc_list[i].link)
    if text:
         examples.append({"text": text, "label": doc_list[i].tipo_documento})


# Classificação dos Outros Documentos
classified_docs = []
for i in range(num_examples, len(doc_list)):
    text = download_and_extract_text(doc_list[i].link)
    if text:
        predicted_label = classify_document(examples, text)
        classified_docs.append({"text": text, "predicted_label": predicted_label})


# Avaliação
correct_predictions = 0
for i, classified_doc in enumerate(classified_docs):
   true_label = doc_list[i+num_examples].tipo_documento
   predicted_label = classified_doc["predicted_label"]
   if true_label == predicted_label:
        correct_predictions += 1


accuracy = correct_predictions / len(classified_docs) if classified_docs else 0


print(f"Acurácia do modelo: {accuracy:.2f}")
print("\nClassificações:")
for classified_doc in classified_docs:
    print(f'Documento: {classified_doc["text"][:50]}...  \nPredição: {classified_doc["predicted_label"]}')