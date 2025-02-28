import sys
import os
import json
import re

# Importa la classe di preprocessing già creata, che gestisce stopwords, lemmatizzazione e stemming
from core.preprocessing.text_processing import SimpleTextProcessor

class KeywordSearchSimilarity:
    MAX_SCORE = 0.3
    PARTIAL_MAX_SCORE = 0.2

    def __init__(self):
        """
        Inizializza la classe per il calcolo della similarità tramite varie tecniche di ricerca di keyword.
        """
        self.processor = SimpleTextProcessor(normalize=False,
                                          remove_special=False,
                                          remove_stop=True,
                                          apply_stemming=True,
                                          apply_lemmatization=True,
                                          language='english') 

    def calculate_similarity(self, keyword, text):
        """
        Calcola la similarità tra una keyword e un testo utilizzando diverse tecniche di matching.
        
        Args:
            keyword (str): Keyword da cercare.
            text (str): Testo in cui cercare la keyword.
        
        Returns:
            float: Punteggio di similarità (1 per exact match, punteggio parziale altrimenti, 0 se nessuna corrispondenza).
        """
        # Uniformizza le stringhe
        keyword = self._uniform_string(keyword)
        text = self._uniform_string(text)
        print("[KEYWORD] Calcolo similarità per keyword:", keyword, "nel testo:", text)

        # Sostituisci gli acronimi
        keyword = self._replace_acronyms(keyword)
        text = self._replace_acronyms(text)
        print("[KEYWORD] Keyword dopo sostituzione acronimi:", keyword)
        print("[KEYWORD] Testo dopo sostituzione acronimi:", text)

        processed_keyword = self.processor.process_custom(keyword)
        processed_text = self.processor.process_custom(text)
        print("[KEYWORD] Keyword processata:", processed_keyword)
        print("[KEYWORD] Testo processato:", processed_text)

        exact_score = self._exact_match(processed_keyword, processed_text)
        if exact_score == self.MAX_SCORE:
            print("[KEYWORD] Exact match trovato dopo preprocessing.")
            return exact_score

        print("[KEYWORD] Exact match non trovato dopo preprocessing, procedo con partial match.")
        partial_score = self._partial_match(processed_keyword, processed_text)
        if partial_score > 0.0:
            print("[KEYWORD] Partial match trovato dopo preprocessing.")
            return partial_score

        print("[KEYWORD] Partial match non trovato, restituisco 0.")
        return 0.0

    def _exact_match(self, keyword, text):
        """
        Verifica se la keyword è presente esattamente nel testo (case-insensitive).
        
        Args:
            keyword (str): La keyword da cercare.
            text (str): Il testo in cui cercare.
        
        Returns:
            float: MAX_SCORE se trovata, 0 altrimenti.
        """
        print("[INFO] Eseguo exact match per keyword:", keyword, "nel testo:", text)
        if keyword.lower() in text.lower():
            return self.MAX_SCORE
        else:
            return 0.0

    def _partial_match(self, search_text, target_text):
        """
        Calcola il punteggio di partial match tra search_text e target_text.
        
        Args:
            search_text (str): Testo di ricerca.
            target_text (str): Testo target.
        
        Returns:
            float: Punteggio di partial match.
        """
        print("[DEBUG] Inizio partial match per:", search_text, "e", target_text)
        search_tokens = search_text.lower().split()
        target_tokens = target_text.lower().split()
        n = len(search_tokens)
        word_found = 0
        for word in search_tokens:
            if word in target_tokens:
                word_found += 1
                print("[DEBUG] Parola trovata:", word, "Totale trovate:", word_found)
        score = (self.PARTIAL_MAX_SCORE / n) * word_found
        print("[DEBUG] Punteggio base partial match:", score)

        print("[DEBUG] Punteggio finale partial match:", score)
        return score

    def _uniform_string(self, text):
        """
        Sostituisce caratteri speciali come '_', '-', '/' con uno spazio e normalizza gli spazi.
        
        Args:
            text (str): Testo da uniformare.
        
        Returns:
            str: Testo uniformato.
        """
        text = re.sub(r'(?<!\w)\.(?!\w{2,4})', ' ', text)
        text = re.sub(r'(?<!\d)\.(?!\d)', ' ', text)
        text = text.replace('_', ' ').replace('-', ' ').replace('/', ' ')\
                   .replace('(', ' ').replace(')', ' ').replace(',', ' ').replace(';', ' ').lower()
        text = ' '.join(text.split()).strip()
        print("[INFO] Testo dopo uniformizzazione:", text)
        return text

    def _replace_acronyms(self, input_string):
        """
        Sostituisce gli acronimi in una stringa caricandoli da un file JSON.
        
        Args:
            input_string (str): Testo in cui sostituire gli acronimi.
        
        Returns:
            str: Testo con acronimi sostituiti.
        """
        acronyms_file = os.path.join(os.path.dirname(__file__), 'acronyms.json')
        with open(acronyms_file, 'r') as f:
            data = json.load(f)
        acronyms = data['acronyms']

        for acronym, expansions in acronyms.items():
            for expansion in expansions:
                pattern_with_acronym = re.compile(r'\b' + re.escape(expansion) + r'\s+' + re.escape(acronym) + r'\b', re.IGNORECASE)
                input_string = pattern_with_acronym.sub(expansion, input_string)
                pattern_acronym_only = re.compile(r'\b' + re.escape(acronym) + r'\b', re.IGNORECASE)
                input_string = pattern_acronym_only.sub(expansion, input_string)

        for acronym, expansions in acronyms.items():
            for expansion in expansions:
                pattern_expansion = re.compile(r'\b' + re.escape(expansion) + r'\b', re.IGNORECASE)
                input_string = pattern_expansion.sub(acronym, input_string)
        return input_string


# Esempio di utilizzo
if __name__ == "__main__":
    keyword = "URL Encoding"
    text = ("The International Domain Name (IDN) support in Opera 7.54 allows remote attackers "
            "to spoof domain names using punycode encoded domain names that are decoded in URLs and SSL "
            "certificates in a way that uses homograph characters from other character sets, which facilitates phishing attacks.")
    keyword_search_sim = KeywordSearchSimilarity()
    similarity_score = keyword_search_sim.calculate_similarity(keyword, text)
    print(f"Calculated Similarity Score: {similarity_score:.4f}")
