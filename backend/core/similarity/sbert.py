from sentence_transformers import SentenceTransformer, util
import os
import torch

class SBERTComparator:
    """
    A class to compare sentences using Sentence-BERT (SBERT).
    Supports both pairwise sentence comparison and comparing a sentence against a list.
    """

    MODEL_DICT = {
        'minilm': 'sentence-transformers/all-MiniLM-L6-v2',
        'distilroberta': 'sentence-transformers/all-distilroberta-v1',
        'mpnet': 'sentence-transformers/paraphrase-mpnet-base-v2',
        'mpnet-large': 'sentence-transformers/all-mpnet-base-v2',
        'bert-base': 'sentence-transformers/bert-base-nli-mean-tokens'
    }

    def __init__(self, model_key='distilroberta', model_name=None, model_dir=None):
        """
        Initializes the SBERT model.
        - model_key: A predefined model key from the dictionary (default: 'mpnet-large').
        - model_name: A custom Hugging Face model name (overrides model_key if provided).
        - model_dir: Custom cache directory for models (default: uses HF_HOME or system cache).
        """

        # If a custom model name is provided, use it; otherwise, get the predefined model
        if model_name is None:
            model_name = self.MODEL_DICT.get(model_key, self.MODEL_DICT['mpnet-large'])

        # 🔹 Use Hugging Face cache directory if available
        self.model_word = "SBERT"
        self.model_dir = model_dir or os.getenv("HF_HOME", "/root/.cache/huggingface")
        # Automatically detect whether CUDA is available
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"Using {self.device}")
        self.model = SentenceTransformer(model_name, cache_folder=self.model_dir).to(self.device)

        print(f"SBERT model loaded: {model_name}")

    def compare_sentences(self, sentence1: str, sentence2: str) -> float:
        """
        Computes cosine similarity between two sentences.

        Args:
            sentence1 (str): First sentence.
            sentence2 (str): Second sentence.

        Returns:
            float: Cosine similarity score.
        """
        embeddings = self.model.encode([sentence1, sentence2], convert_to_tensor=True, device=self.device)
        similarity = util.pytorch_cos_sim(embeddings[0], embeddings[1]).item()
        return similarity

    def compare_with_list(self, sentence: str, sentence_list: list) -> list:
        """
        Computes similarity between a given sentence and a list of sentences.

        Args:
            sentence (str): The sentence to compare.
            sentence_list (list): A list of sentences to compare against.

        Returns:
            list: A sorted list of tuples (sentence, similarity_score), in descending order.
        """
        sentence_embedding = self.model.encode(sentence, convert_to_tensor=True, device=self.device)
        list_embeddings = self.model.encode(sentence_list, convert_to_tensor=True, device=self.device)
        similarities = util.pytorch_cos_sim(sentence_embedding, list_embeddings)[0]

        results = [(sentence_list[i], similarities[i].item()) for i in range(len(sentence_list))]
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def compare_with_list_in_order(self, sentence: str, sentence_list: list) -> list:
        """
        Computes similarity between a given sentence and a list of sentences,
        returning only the similarity scores in the same order as the input sentence_list.

        Args:
            sentence (str): The sentence to compare.
            sentence_list (list): A list of sentences to compare against.

        Returns:
            list: A list of similarity scores corresponding to each sentence in sentence_list,
                preserving the original order.
        """
        sentence_embedding = self.model.encode(sentence, convert_to_tensor=True, device=self.device)
        list_embeddings = self.model.encode(sentence_list, convert_to_tensor=True, device=self.device)
        similarities = util.pytorch_cos_sim(sentence_embedding, list_embeddings)[0]
        return [similarities[i].item() for i in range(len(sentence_list))]


    @classmethod
    def available_models(cls):
        """Returns the dictionary of available SBERT models."""
        return cls.MODEL_DICT

if __name__ == "__main__":
    comparator = SBERTComparator(model_key="minilm")  # Using MiniLM model
    print(comparator.compare_sentences("Hello, how are you?", "Hi, how's it going?"))
    
    sentence = "Artificial intelligence is evolving rapidly."
    sentence_list = [
        "Machine learning is a subset of AI.",
        "Deep learning is a type of machine learning.",
        "The weather is nice today."
    ]
    results = comparator.compare_with_list(sentence, sentence_list)
    print("Similarity with list:", results)

    # Print available models
    print("Available SBERT models:", SBERTComparator.available_models())
