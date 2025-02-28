import os
from core.tasks.utils import _get_model, _get_capecs, _get_cves, _get_task, _create_single_correlation, _rank_capecs
from core.similarity.keyword import KeywordSearchSimilarity
from core.preprocessing.text_processing import SimpleTextProcessor

from celery import shared_task

@shared_task(queue="heavy_tasks")
def process_cve_subgroup(cve_list, task_id):
    """
    Processa un sottogruppo di CVE:
      - Stampa informazioni di debug (ID processo, task_id, numero e lista di CVE).
      - Recupera la Task dal database e il relativo attributo "ai_models".
      - In base al valore di ai_models, istanzia il modello di comparazione corrispondente.
      - Recupera le CVE dal database (filtrando per ID) e i CAPEC con Status diverso da "Deprecated".
      - Per ogni CVE, chiama la funzione _process_single_cve.
      - Gestisce eventuali errori ed eccezioni.
      
    Args:
        cve_list (list): Lista di ID CVE da processare.
        task_id (int): ID della task da processare.
    
    Returns:
        dict: {'status': 'processed'} in caso di esecuzione corretta o un dizionario di errore.
    """
    #print(f"[DEBUG] Process ID: {os.getpid()}")
    #print(f"[DEBUG] Task ID ricevuto: {task_id}")
    #print(f"[DEBUG] Numero di CVE da processare: {len(cve_list)}")
    #print(f"[DEBUG] Lista di CVE da processare: {cve_list}")
    
    try:
        # 1) Recupera la task e il modello AI
        task = _get_task(task_id)
        ai_model_type = task.ai_models
        model = _get_model(ai_model_type)

        # Recupera le CVE dal database
        cves = _get_cves(cve_list)
        #print(f"[DEBUG] Numero di CVE trovate nel database: {cves.count()}")

        # Processa ogni CVE
        for cve in cves:
            #print(f"[DEBUG] Tipo di cve: {type(cve)} - Valore: {cve}")  # Controlla il tipo di oggetto
            process_single_cve(cve, task_id, model)
            #print(f"[DEBUG] Terminato processing per CVE {cve.id}")

    except Exception as e:
        print(f"[ERROR] Errore durante il processamento del gruppo: {str(e)}")
        return {'status': 'error', 'message': str(e)}

    return {'status': 'processed'}


def process_single_cve(cve, task_id, model):
    # Usa l'ID del processo per identificare il worker di Celery
    try:
        log_line = f"[DEBUG] Processing CVE {cve.id} per Task {task_id} con modello {model.__class__.__name__}\n"

        semantic_results = {}
        semantic_scores = get_semantic_similarity_scores(cve, model)
        semantic_results[model.model_word] = semantic_scores

        log_line = f"Scores ottenuti per modello {model} e CVE {cve.id}: {semantic_scores}\n"

        keyword_scores = get_keyword_similarity_scores(cve)
        log_line = f"Keyword scores: {keyword_scores}\n"

        hybrid_scores = integrate_keyword_scores(semantic_results, keyword_scores)
        log_line = f"Hybrid scores: {hybrid_scores}\n"

        _create_single_correlation(cve.id, hybrid_scores, task_id)

        result = {"status": "processed"}
    except Exception as e:
        result = {"status": "error", "message": str(e)}

    return result


def get_semantic_similarity_scores(cve, model):
    """
    Confronta una descrizione di una CVE con un CAPEC, utilizzando modelli AI per calcolare la similarità.

    :param cleaned_cve_description: La descrizione della CVE preprocessata.
    :param capec: L'oggetto CAPEC da confrontare con la CVE.
    :param ai_model: Il modello AI da utilizzare per il confronto (ad esempio 'SBERT' o 'ATTACKBERT').

    :return: Un dizionario contenente i punteggi di similarità per ogni CAPEC.
    """
    
    capec_similarity_scores = {}  # Dizionario per memorizzare i punteggi di tutte le CAPEC
    text_processor = SimpleTextProcessor()
    preprocessed_cve_description = text_processor.process_custom(cve.description)
    #print(f"Descrizione CVE ripulita: {preprocessed_cve_description}")
    capec_list = _get_capecs() 

    for capec in capec_list:
        
        capec_id = capec.id  # Usa l'ID della CAPEC per associare i punteggi
        
        # Inizializza un dizionario per questa CAPEC, se non esiste
        if capec_id not in capec_similarity_scores:
            capec_similarity_scores[capec_id] = {}

        # 1. Estrai tutti i campi aggregati da CAPEC in una lista (esclusi quelli non validi)
        capec_aggregated_fields = []
        field_names = []

        # Funzione per controllare se il campo è valido (non None e non vuoto)
        def is_valid_field(field):
            return field is not None and field != ""

        # Aggiungi i campi validi a capec_aggregated_fields e aggiorna i field_names
        if is_valid_field(capec.name):
            capec_aggregated_fields.append(text_processor.process_custom(capec.name))
            field_names.append('name')
        if is_valid_field(capec.description_aggregated):
            capec_aggregated_fields.append(text_processor.process_custom(capec.description_aggregated))
            field_names.append('description')                
        if is_valid_field(capec.prerequisites_aggregated):
            capec_aggregated_fields.append(text_processor.process_custom(capec.prerequisites_aggregated))
            field_names.append('prerequisites')           
        if is_valid_field(capec.resources_required_aggregated):
            capec_aggregated_fields.append(text_processor.process_custom(capec.resources_required_aggregated))
            field_names.append('resources_required')            
        if is_valid_field(capec.mitigations_aggregated):
            capec_aggregated_fields.append(text_processor.process_custom(capec.mitigations_aggregated))
            field_names.append('mitigations')           
        if is_valid_field(capec.skills_required_aggregated):
            capec_aggregated_fields.append(text_processor.process_custom(capec.skills_required_aggregated))
            field_names.append('skills_required')
        if is_valid_field(capec.extended_description_aggregated):
            capec_aggregated_fields.append(text_processor.process_custom(capec.extended_description_aggregated))
            field_names.append('extended_description')       
        if is_valid_field(capec.indicators_aggregated):
            capec_aggregated_fields.append(text_processor.process_custom(capec.indicators_aggregated))
            field_names.append('indicators')  
        #if is_valid_field(capec.example_instances_aggregated):
            #capec_aggregated_fields.append(text_processor.process_custom(capec.example_instances_aggregated))
            #field_names.append('example_instances')
                
        # Calcola la similarità batch usando il modello AI con i campi aggregati
        
        similarity_scores = model.compare_with_list_in_order(preprocessed_cve_description, capec_aggregated_fields)
        
        # Associare i punteggi di similarità ai nomi dei campi
        field_similarity = []
        for idx, score in enumerate(similarity_scores):
            field_similarity.append((field_names[idx], score))

        executionflow_aggregated_fields = []  # Lista per i punteggi massimi
        executionflow_field_names = []  # Lista per i nomi dei campi
        executionflow_average_score = 0
        attack_description_list = []  # Lista per le description degli attack step
        attack_techniques_list = []  # Lista per le techniques degli attack step

        # Verifica se il CAPEC dispone dell'attributo execution_flow e non è None
        if hasattr(capec, "execution_flow_instance") and capec.execution_flow_instance is not None:         
            attack_step_count = 0
            attack_description_names = []
            attack_technique_names = []
        
            for idx, attack_step in enumerate(capec.execution_flow.attack_steps.all()):
                description_valid = is_valid_field(attack_step.description_aggregated)
                techniques_valid = is_valid_field(attack_step.techniques_aggregated)
                
                if description_valid or techniques_valid:
                    attack_step_count += 1
                    # Aggiungi alla lista per la comparazione batch
                    if description_valid:
                        attack_description_list.append(text_processor.process_custom(attack_step.description_aggregated))
                        attack_description_names.append(f'attack_step_{idx+1}_description')
                    if techniques_valid:
                        attack_techniques_list.append(text_processor.process_custom(attack_step.techniques_aggregated))
                        attack_technique_names.append(f'attack_step_{idx+1}_techniques')

            # Esegui la comparazione per description e techniques insieme
            if attack_step_count > 0:
                execution_flow_combined_list = attack_description_list + attack_techniques_list    

                attack_step_similarity_scores = model.compare_with_list_in_order(preprocessed_cve_description, execution_flow_combined_list)
                
                # 3. Associare i punteggi di similarità ai nomi dei campi
                field_similarity_for_attack_steps = []

                # Prima aggiungiamo i nomi delle descrizioni
                for idx, score in enumerate(attack_step_similarity_scores[:len(attack_description_names)]):
                    field_similarity_for_attack_steps.append((attack_description_names[idx], score))

                # Poi aggiungiamo i nomi delle tecniche
                for idx, score in enumerate(attack_step_similarity_scores[len(attack_description_names):len(attack_description_names) + len(attack_technique_names)]):
                    field_similarity_for_attack_steps.append((attack_technique_names[idx], score))

                for i in range(attack_step_count):
                    attack_description_score = 0  # Imposta direttamente a 0
                    attack_techniques_score = 0  # Imposta direttamente a 0

                    for field_name, score in field_similarity_for_attack_steps:
                        if field_name == f'attack_step_{i+1}_description':
                            attack_description_score = score                         
                        if field_name == f'attack_step_{i+1}_techniques':
                            attack_techniques_score = score
                            
                    # Calcola il massimo tra description e techniques per il passo d'attacco
                    max_score = max(attack_description_score, attack_techniques_score)

                    # Memorizza il punteggio massimo
                    executionflow_aggregated_fields.append(max_score)
                    executionflow_field_names.append(f'attack_step_{i+1}_max_score')

            # Calcola la media dei punteggi aggregati
            if executionflow_aggregated_fields:
                executionflow_average_score = sum(executionflow_aggregated_fields) / len(executionflow_aggregated_fields)
        else:
            # Se il CAPEC non ha execution_flow, logga un warning e imposta il punteggio a 0 (o a un valore predefinito)
            #print(f"[WARNING] CAPEC {capec.id} has no execution_flow. Skipping execution flow processing.")
            executionflow_average_score = 0

        # Aggiungi i punteggi per questa CAPEC al dizionario capec_similarity_scores
        for field_name, score in field_similarity:

            # Assicurati che capec_similarity_scores[capec_id] sia un dizionario
            if isinstance(capec_similarity_scores[capec_id], dict):
                capec_similarity_scores[capec_id][f'{field_name}_score'] = round(score, 3)        
                
        # Aggiungi il punteggio massimo (execution_flow_score) per questa CAPEC
        if executionflow_average_score:
            capec_similarity_scores[capec_id]['execution_flow_score'] = executionflow_average_score

        # Imposta a 0 tutti i valori negativi in capec_similarity_scores[capec_id]
        for field, score in capec_similarity_scores[capec_id].items():
            if score < 0:
                capec_similarity_scores[capec_id][field] = 0

        # Aggiungi il punteggio finale per la CAPEC (media di tutti i punteggi)
        if capec_similarity_scores[capec_id]:
            total_score = sum(capec_similarity_scores[capec_id].values())  # Somma tutti i punteggi
            total_count = len(capec_similarity_scores[capec_id])  # Conta quanti punteggi ci sono
            final_score = total_score / total_count  # Calcola il punteggio medio finale

            # Aggiungi il punteggio medio finale
            capec_similarity_scores[capec_id]['final_score'] = round(final_score, 3)
  
    # Ordina i CAPECs per 'final_score' in ordine decrescente
    capec_ranked_scores = sorted(capec_similarity_scores.items(), key=lambda x: float(x[1].get('final_score', 0)), reverse=True)
    
    # Aggiungi il rank a ciascun CAPEC ordinato
    for rank, (capec_id, score_data) in enumerate(capec_ranked_scores, start=1):
        score_data['rank'] = rank

    # Restituisci il dizionario capec_similarity_scores
    return capec_ranked_scores

def get_keyword_similarity_scores(cve):
    """
    Processa le CAPEC fornite utilizzando un modello di similarità basato su keyword.

    :param keyword_model: Modello per calcolare la similarità tra testo.
    :param cleaned_cve_description: Descrizione CVE preprocessata.
    :param capecs_to_use: Lista di CAPEC da analizzare.
    :return: Dizionario dei punteggi di similarità delle keyword per ciascuna CAPEC.
    """
    def is_valid_field(field):
        """Verifica se un campo è valido (non None e non vuoto)."""
        return field is not None and field != ""

    try:
        keyword_similarity_scores = {}
        text_processor = SimpleTextProcessor()
        keyword_model = KeywordSearchSimilarity()
        preprocessed_cve_description = text_processor.process_custom(cve.description)
        #print(f"Descrizione CVE ripulita: {preprocessed_cve_description}")
        capec_list = _get_capecs() 
        for capec in capec_list:
            try:
                capec_id = capec.id  

                # Inizializza punteggio e struttura
                keyword_score = 0
                keyword_similarity_scores.setdefault(capec_id, {})

                # Calcola la similarità per i campi principali della CAPEC
                if is_valid_field(capec.name):
                    keyword_score = max(keyword_score, keyword_model.calculate_similarity(capec.name, preprocessed_cve_description))

                # Calcola la similarità per i termini alternativi, se presenti
                if is_valid_field(capec.alternate_terms):
                    for term in capec.alternate_terms:
                        try:
                            term_score = keyword_model.calculate_similarity(term, preprocessed_cve_description)
                            keyword_score = max(keyword_score, term_score)
                        except Exception as e:
                            print(f"Error calculating similarity for term '{term}': {e}")

                # Salva il punteggio arrotondato
                keyword_similarity_scores[capec_id]['keyword_score'] = round(keyword_score, 3)

            except Exception as capec_error:
                print(f"Error processing CAPEC with ID {capec_id}: {capec_error}")
                continue

        return keyword_similarity_scores

    except Exception as e:
        print(f"Critical error in process_cve_keywords: {e}")
        return {}
    
def integrate_keyword_scores(similarity_results, keyword_scores):
    """
    Integra i punteggi di keyword nei risultati di similarità e calcola i rank aggiornati.

    :param similarity_results: Dizionario con i risultati di similarità per ciascun modello.
    :param keyword_scores: Dizionario con i punteggi di keyword per ciascuna CAPEC.
    :return: Dizionario aggiornato con i nuovi modelli "_keyword".
    """
    try:
        updated_results = similarity_results.copy()

        for model_name, capec_scores in similarity_results.items():
            # Nome del nuovo modello con keyword
            keyword_model_name = f"{model_name}_keyword"
            updated_results[keyword_model_name] = []

            for capec_id, score_data in capec_scores:
                try:
                    # Prendi il punteggio originale
                    original_final_score = score_data.get("final_score", 0)

                    # Integra il keyword score
                    keyword_score = keyword_scores.get(capec_id, {}).get("keyword_score", 0)
                    combined_score = original_final_score + keyword_score

                    # Crea il nuovo dizionario per il modello _keyword
                    new_score_data = score_data.copy()
                    new_score_data["final_score"] = round(combined_score, 3)
                    updated_results[keyword_model_name].append([capec_id, new_score_data])
                except Exception as e:
                    print(f"Error integrating scores for CAPEC {capec_id}: {e}")
                    continue

            # Ordina e calcola i rank per il nuovo modello
            updated_results[keyword_model_name] = _rank_capecs(updated_results[keyword_model_name])

        return updated_results
    except Exception as e:
        print(f"Critical error in integrate_keyword_scores: {e}")
        return {}


