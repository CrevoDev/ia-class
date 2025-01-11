import io
import base64
import requests
from PIL import Image
import pytesseract
from pdf2image import convert_from_bytes
import PyPDF2
from requests.exceptions import RequestException

class FileService:
    @staticmethod
    def convert_drive_link_to_download(url):
        if "drive.google.com" in url:
            file_id = url.split('/d/')[1].split('/')[0]
            return f"https://drive.google.com/uc?export=download&id={file_id}"
        return url

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def download_and_extract_text(url):
        try:
            download_url = FileService.convert_drive_link_to_download(url)
            response = requests.get(download_url, timeout=10)
            response.raise_for_status()
            pdf_content = response.content
            text = FileService.extract_text_from_pdf(pdf_content)
            if not text.strip():
                text = FileService.extract_text_from_scanned_pdf(pdf_content)
            return text
        except RequestException as e:
            print(f"Erro ao baixar ou processar o arquivo: {url} - {e}")
            return None