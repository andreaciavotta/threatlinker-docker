import os
import re
import string
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer, WordNetLemmatizer

class SimpleTextProcessor:
    _nltk_initialized = False

    @classmethod
    def init_nltk(cls):
        """Inizializza NLTK (scaricando i dati se necessario) una sola volta per processo."""
        if cls._nltk_initialized:
            return
        # Imposta la directory in cui NLTK salverà i dati (deve essere scrivibile)
        nltk_data_dir = os.environ.get('NLTK_DATA', '/app/nltk_data')
        os.environ['NLTK_DATA'] = nltk_data_dir

        if not os.path.exists(nltk_data_dir):
            os.makedirs(nltk_data_dir, exist_ok=True)

        # Scarica le risorse necessarie se ENABLE_NLTK è abilitato
        if os.environ.get("ENABLE_NLTK", "true").lower() == "true":
            for resource in ['stopwords', 'wordnet', 'omw-1.4']:
                try:
                    nltk.data.find(f'corpora/{resource}')
                except LookupError:
                    nltk.download(resource, download_dir=nltk_data_dir)
        cls._nltk_initialized = True

    def __init__(self, normalize=True, remove_special=True, remove_stop=True,
                 apply_stemming=False, apply_lemmatization=False, language='english'):
        """
        Inizializza gli strumenti di preprocessing e imposta i parametri di default.
        Il download di NLTK verrà eseguito una sola volta (quando viene istanziata la classe).
        """
        self.init_nltk()  # Inizializza NLTK se non è già stato fatto

        self.normalize_flag = normalize
        self.remove_special_flag = remove_special
        self.remove_stop_flag = remove_stop
        self.apply_stemming_flag = apply_stemming
        self.apply_lemmatization_flag = apply_lemmatization
        self.language = language
        
        # Inizializza gli strumenti di NLP
        self.stemmer = PorterStemmer()
        self.lemmatizer = WordNetLemmatizer()

    def _normalize(self, text):
        """Converte il testo in minuscolo."""
        return text.lower()

    def _remove_special_characters(self, text):
        """
        Rimuove tabulazioni, newline, punteggiatura e caratteri speciali,
        normalizzando gli spazi multipli.
        """
        text = re.sub(r'[\t\n\r]', ' ', text)
        text = re.sub(r'[' + re.escape(string.punctuation) + ']', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def _remove_stop_words(self, text, language='english'):
        """Rimuove le stop words dal testo."""
        tokens = text.split()
        stops = set(stopwords.words(language))
        tokens = [token for token in tokens if token not in stops]
        return ' '.join(tokens)

    def _stemming(self, text):
        """Applica lo stemming ai token del testo."""
        tokens = text.split()
        tokens = [self.stemmer.stem(token) for token in tokens]
        return ' '.join(tokens)

    def _lemmatization(self, text):
        """Applica la lemmatizzazione ai token del testo."""
        tokens = text.split()
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        return ' '.join(tokens)

    def process_custom(self, text, normalize=None, remove_special=None, remove_stop=None,
                       apply_stemming=None, apply_lemmatization=None, language=None):
        """
        Processa il testo applicando in sequenza le funzioni di preprocessing.
        Se un parametro non viene specificato, verrà usato il valore di default impostato al costruttore.

        Parametri:
            text (str): il testo da processare.
            normalize (bool): se True, converte il testo in minuscolo.
            remove_special (bool): se True, rimuove punteggiatura, spazi, tab e caratteri speciali.
            remove_stop (bool): se True, rimuove le stop words.
            apply_stemming (bool): se True, applica lo stemming.
            apply_lemmatization (bool): se True, applica la lemmatizzazione.
            language (str): la lingua da usare per la rimozione delle stop words.

        Restituisce:
            str: il testo processato.
        """
        # Usa i parametri di default se non specificati
        normalize = self.normalize_flag if normalize is None else normalize
        remove_special = self.remove_special_flag if remove_special is None else remove_special
        remove_stop = self.remove_stop_flag if remove_stop is None else remove_stop
        apply_stemming = self.apply_stemming_flag if apply_stemming is None else apply_stemming
        apply_lemmatization = self.apply_lemmatization_flag if apply_lemmatization is None else apply_lemmatization
        language = self.language if language is None else language

        result = text
        if normalize:
            result = self._normalize(result)
        if remove_special:
            result = self._remove_special_characters(result)
        if remove_stop:
            result = self._remove_stop_words(result, language)
        if apply_stemming:
            result = self._stemming(result)
        if apply_lemmatization:
            result = self._lemmatization(result)
        return result
