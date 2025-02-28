from transformers import AutoTokenizer, AutoModel
import torch
from sentence_transformers import util
import os

class AttackBERTComparator:
    """
    Una classe per confrontare frasi utilizzando il modello ATTACK-BERT.
    Supporta sia il confronto fra due frasi sia il confronto di una frase rispetto a una lista.
    """
    
    MODEL_DICT = {
        'attackbert': 'basel/ATTACK-BERT'
    }
    
    def __init__(self, model_key='attackbert', model_name=None, model_dir=None):
        """
        Inizializza il modello ATTACK-BERT.
        
        Args:
            model_key (str): chiave predefinita del modello (default: 'attackbert').
            model_name (str): nome custom del modello (se fornito, sovrascrive model_key).
            model_dir (str): directory per la cache dei modelli.
        """
        # Se non viene fornito un nome custom, usa quello presente in MODEL_DICT
        if model_name is None:
            model_name = self.MODEL_DICT.get(model_key, self.MODEL_DICT['attackbert'])
        
        self.model_word = "ATTACKBERT"
        self.model_name = model_name
        self.model_dir = model_dir or os.getenv("HF_HOME", "/root/.cache/huggingface")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Utilizzo dispositivo: {self.device}")
        
        # Carica tokenizer e modello da Hugging Face
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name, cache_dir=self.model_dir)
        self.model = AutoModel.from_pretrained(self.model_name, cache_dir=self.model_dir)
        self.model.to(self.device)
        self.model.eval()  # Modalità evaluation per disabilitare dropout
        
        print(f"Modello ATTACK-BERT caricato: {self.model_name}")
    
    def encode(self, sentences):
        """
        Codifica una o più frasi in embeddings.
        
        Args:
            sentences (str or list): frase o lista di frasi da codificare.
        
        Returns:
            torch.Tensor: embeddings delle frasi.
        """
        if isinstance(sentences, str):
            sentences = [sentences]
        inputs = self.tokenizer(
            sentences,
            return_tensors='pt',
            padding=True,
            truncation=True,
            max_length=512
        )
        inputs = {key: value.to(self.device) for key, value in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
        # Calcola il mean pooling sui token embeddings
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings
    
    def compare_sentences(self, sentence1: str, sentence2: str) -> float:
        """
        Calcola la similarità coseno tra due frasi.
        
        Args:
            sentence1 (str): Prima frase.
            sentence2 (str): Seconda frase.
        
        Returns:
            float: Punteggio di similarità.
        """
        embeddings = self.encode([sentence1, sentence2])
        similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
        return similarity
    
    def compare_with_list(self, sentence: str, sentence_list: list) -> list:
        """
        Confronta una frase con una lista di frasi e restituisce una lista di tuple 
        (frase, punteggio di similarità) ordinate in ordine decrescente.
        
        Args:
            sentence (str): La frase di riferimento.
            sentence_list (list): Lista di frasi da confrontare.
        
        Returns:
            list: Lista ordinata di tuple (frase, punteggio).
        """
        sentence_embedding = self.encode(sentence)
        list_embeddings = self.encode(sentence_list)
        similarities = util.pytorch_cos_sim(sentence_embedding, list_embeddings)[0]
        results = [(sentence_list[i], similarities[i].item()) for i in range(len(sentence_list))]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def compare_with_list_in_order(self, sentence: str, sentence_list: list) -> list:
        """
        Confronta una frase con una lista di frasi e restituisce una lista dei punteggi di similarità,
        mantenendo l'ordine originale della lista di input.
        
        Args:
            sentence (str): La frase di riferimento.
            sentence_list (list): Lista di frasi da confrontare.
        
        Returns:
            list: Lista dei punteggi di similarità corrispondenti alle frasi in sentence_list, nell'ordine originale.
        """
        sentence_embedding = self.encode(sentence)
        list_embeddings = self.encode(sentence_list)
        similarities = util.pytorch_cos_sim(sentence_embedding, list_embeddings)[0]
        return [similarities[i].item() for i in range(len(sentence_list))]


    @classmethod
    def available_models(cls):
        """Restituisce il dizionario dei modelli ATTACK-BERT disponibili."""
        return cls.MODEL_DICT


if __name__ == "__main__":
    comparator = AttackBERTComparator()
    sim = comparator.compare_sentences("Ciao, come stai?", "Salve, come va?")
    print("Similarità tra le frasi:", sim)
    
    sentence = "L'intelligenza artificiale sta progredendo rapidamente."
    sentence_list = [
        "Il machine learning è una branca dell'IA.",
        "Il deep learning è una tecnica avanzata.",
        "Oggi il tempo è bello."
    ]
    results = comparator.compare_with_list(sentence, sentence_list)
    print("Similarità con la lista:", results)
    
    print("Modelli ATTACK-BERT disponibili:", AttackBERTComparator.available_models())
