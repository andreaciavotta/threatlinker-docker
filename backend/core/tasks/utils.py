from core.similarity.sbert import SBERTComparator
from core.similarity.attackbert import AttackBERTComparator
from core.tasks.task_config import SBERT_MODEL
from core.models.task import SingleCorrelation, Task
from data.models import CVE, CAPEC

def _get_task(task_id):
    """Recupera la Task dal database tramite il model in core.models."""
    try:
        task = Task.objects.get(id=task_id)
        return task
    except Task.DoesNotExist:
        raise Exception(f"Task con ID {task_id} non trovata.")

def _get_cves(cve_list):
    """
    Recupera dal database le CVE il cui id è presente in cve_list.
    """
    cves = CVE.objects.filter(id__in=cve_list)
    return cves

def _get_capecs():
    """
    Recupera dal database i CAPEC che non hanno lo Status 'Deprecated'.
    """
    capecs = CAPEC.objects.exclude(status="Deprecated")
    return capecs

def _get_model(ai_model_type):
    """
    In base al valore di ai_model_type, istanzia il modello corrispondente.
    Supporta "SBERT Hyb" e "ATTACKBERT Hyb".
    """
    # Se ai_model_type è una lista, prendi il primo elemento
    if isinstance(ai_model_type, list):
        if ai_model_type:
            ai_model_type = ai_model_type[0]
        else:
            raise Exception("ai_model_type è una lista vuota.")

    if ai_model_type == "SBERT Hyb":      
        #print(f"[DEBUG] Istanzio SBERTComparator per ai_models='{ai_model_type}'")
        return SBERTComparator(model_key=SBERT_MODEL)
    elif ai_model_type == "ATTACKBERT Hyb":       
        #print(f"[DEBUG] Istanzio ATTACKBERTComparator per ai_models='{ai_model_type}'")
        return AttackBERTComparator()
    else:
        raise Exception(f"Tipo di modello AI non supportato: {ai_model_type}")

def _create_single_correlation(cve_id, similarity_scores, task_id):
    """
    Crea una relazione di correlazione per una CVE con i risultati di similarità.

    :param cve_id: ID della CVE.
    :param similarity_scores: Risultati di similarità calcolati.
    :param task: Oggetto Task associato.
    :return: None.
    """
    try:
        task = _get_task(task_id)
        SingleCorrelation.objects.create(
            cve_id=cve_id,
            similarity_scores=similarity_scores,
            status="complete",
            task=task
        )
        print(f"SingleCorrelation created for CVE {cve_id}.")
    except Exception as e:
        print(f"Error creating SingleCorrelation for CVE {cve_id}: {e}")
        raise

    
def _rank_capecs(capec_scores):
    """
    Ordina le CAPEC per 'final_score' in ordine decrescente e calcola i rank.

    :param capec_scores: Lista di CAPEC con i punteggi.
    :return: Lista di CAPEC ordinata e rankata.
    """
    try:
        # Ordina per final_score in ordine decrescente
        capec_ranked_scores = sorted(
            capec_scores,
            key=lambda x: float(x[1].get("final_score", 0)),
            reverse=True
        )

        # Aggiungi il rank
        for rank, (capec_id, score_data) in enumerate(capec_ranked_scores, start=1):
            score_data["rank"] = rank

        return capec_ranked_scores
    except Exception as e:
        print(f"Error ranking CAPECs: {e}")
        return capec_scores