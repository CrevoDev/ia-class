import time
import pandas as pd
from dtos.document_dto import DocumentDTO
from services.file_service import FileService
from services.classification_service import ClassificationService
from maps.field_map import FieldMap

class App:
    def __init__(self, csv_file_path):
        self.csv_file_path = csv_file_path
        self.doc_list = []
        self.examples = []
        self.classified_docs = []

    def load_data(self):
        df = pd.read_csv(self.csv_file_path)
        df.rename(columns=FieldMap.get_field_mapping(), inplace=True)
        self.doc_list = [DocumentDTO(**doc) for doc in df.to_dict(orient='records')]

    def download_and_extract_texts(self):
        print("Baixando e extraindo texto dos documentos...")
        for doc in self.doc_list:
            doc.text = FileService.download_and_extract_text(doc.link)

    def prepare_examples(self):
        print("Preparando exemplos...")
        num_examples = min(5, len(self.doc_list))  # Limita o número de exemplos
        self.examples = []
        for i in range(num_examples):
            if self.doc_list[i].text:
                self.examples.append({"text": self.doc_list[i].text, "label": self.doc_list[i].tipo_documento})

    def classify_documents(self):
        print("Classificando documentos restantes...")
        self.classified_docs = []
        for i in range(len(self.examples), len(self.doc_list)):
            if self.doc_list[i].text:
                predicted_label = ClassificationService.classify_document(self.examples, self.doc_list[i].text)
                self.classified_docs.append({"text": self.doc_list[i].text, "predicted_label": predicted_label})

    def evaluate_results(self):
        print("Avaliando resultados...")
        correct_predictions = 0
        for i, classified_doc in enumerate(self.classified_docs):
            true_label = self.doc_list[i+len(self.examples)].tipo_documento
            predicted_label = classified_doc["predicted_label"]
            if true_label == predicted_label:
                correct_predictions += 1

        accuracy = correct_predictions / len(self.classified_docs) if self.classified_docs else 0
        print(f"Acurácia do modelo: {accuracy:.2f}")
        print("\nClassificações:")
        for classified_doc in self.classified_docs:
            print(f'Documento: {classified_doc["text"][:50]}...  \nPredição: {classified_doc["predicted_label"]}')

    def run(self):
        self.load_data()
        self.download_and_extract_texts()
        ClassificationService.configure_model()
        self.prepare_examples()
        self.classify_documents()
        self.evaluate_results()
