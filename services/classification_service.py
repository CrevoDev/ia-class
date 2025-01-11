import time
from google.api_core.exceptions import ResourceExhausted
from services.gemini_service import GeminiService

class ClassificationService:
    model = None

    @staticmethod
    def configure_model():
        ClassificationService.model = GeminiService.configure()

    @staticmethod
    def create_prompt(examples, new_document):
        """Cria um prompt com exemplos e instruções para classificação."""
        print("Criando prompt...")
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

    @staticmethod
    def classify_document(examples, document_text, retry_count=3, delay=5):
        """Classifica um documento usando o modelo Gemini."""
        print("Classificando documento...")
        prompt = ClassificationService.create_prompt(examples, document_text)
        try:
            response = GeminiService.generate_content(ClassificationService.model, prompt)
            return response.text.strip()
        except ResourceExhausted as e:
            if retry_count > 0:
                print(f"Limite atingido. Esperando {delay} segundos e tentando novamente... ({retry_count} tentativas restantes)")
                time.sleep(delay)
                return ClassificationService.classify_document(examples, document_text, retry_count - 1, delay * 2) # aumenta o delay em dobro
            else:
                print(f"Erro: Limite de uso da API atingido após várias tentativas: {e}")
                return None
