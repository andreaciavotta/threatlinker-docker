import os
import requests
import xml.etree.ElementTree as ET
from data.models import CAPEC, ExecutionFlow, AttackStep, CAPECRelatedAttackPattern

CAPEC_URL = "https://capec.mitre.org/data/xml/capec_latest.xml"

def remove_namespace(tree):
    for elem in tree.iter():
        if '}' in elem.tag:
            elem.tag = elem.tag.split('}', 1)[1]
    return tree

def clean_text(text):
    return ' '.join(text.split()).strip() if text else None

def extract_cleaned_text(element):
    if element is None:
        return None
    text_content = ''.join(element.itertext())
    return clean_text(text_content)

def download_capec_data():
    """Scarica il file CAPEC da MITRE e lo salva in download/capec_latest.xml"""
    
    download_dir = "download"
    file_path = os.path.join(download_dir, "capec_latest.xml")

    # Crea la directory se non esiste
    os.makedirs(download_dir, exist_ok=True)

    print("Scaricando il file CAPEC...")
    response = requests.get(CAPEC_URL, stream=True)

    if response.status_code == 200:
        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"File scaricato con successo: {file_path}")
        return file_path
    else:
        raise Exception(f"Errore durante il download: {response.status_code}")

def import_capec_data():
    """Importa i dati CAPEC nel database solo se non sono già presenti"""

    # Scarica il file CAPEC se non esiste già
    file_path = "download/capec_latest.xml"
    if not os.path.exists(file_path):
        file_path = download_capec_data()

    # Caricamento del file XML
    try:
        tree = ET.parse(file_path)
        tree = remove_namespace(tree)
        root = tree.getroot()
    except Exception as e:
        raise ValueError(f"Errore durante il parsing del file XML: {e}")

    # Controllo del catalogo CAPEC
    catalog_name = root.attrib.get("Name")
    version = root.attrib.get("Version")
    date = root.attrib.get("Date")

    if catalog_name != "CAPEC":
        raise ValueError("Il file XML non è un catalogo CAPEC valido.")

    # Creazione dei pattern CAPEC
    capec_instances = {}
    for pattern in root.findall('.//Attack_Pattern'):
        capec_id = f"CAPEC-{pattern.get('ID')}"
        name = pattern.get('Name')
        abstraction = pattern.get('Abstraction')
        status = pattern.get('Status')

        description = extract_cleaned_text(pattern.find('Description'))
        extended_description = extract_cleaned_text(pattern.find('Extended_Description'))
        likelihood_of_attack = clean_text(pattern.findtext('Likelihood_Of_Attack'))
        typical_severity = clean_text(pattern.findtext('Typical_Severity'))

        prerequisites = [extract_cleaned_text(prereq) for prereq in pattern.findall('Prerequisites/Prerequisite')]

        skills_required = [{
            "Level": skill.get("Level"),
            "Description": extract_cleaned_text(skill)
        } for skill in pattern.findall('Skills_Required/Skill')]

        resources_required = [extract_cleaned_text(resource) for resource in pattern.findall('Resources_Required/Resource')]

        indicators = [extract_cleaned_text(indicator) for indicator in pattern.findall('Indicators/Indicator')]
              
        alternate_terms = [extract_cleaned_text(term) for term in pattern.findall('.//Alternate_Terms/Alternate_Term/Term')] 
        
        consequences = [{
            "Scope": [clean_text(scope.text) for scope in consequence.findall('Scope')],
            "Impact": [clean_text(impact.text) for impact in consequence.findall('Impact')],
            "Note": extract_cleaned_text(consequence.find('Note'))
        } for consequence in pattern.findall('Consequences/Consequence')]

        mitigations = [extract_cleaned_text(mitigation) for mitigation in pattern.findall('Mitigations/Mitigation')]

        example_instances = [extract_cleaned_text(example) for example in pattern.findall('Example_Instances/Example')]

        capec_data = {
            "name": name,
            "abstraction": abstraction,
            "status": status,
            "description": description,
            "extended_description": extended_description,
            "likelihood_of_attack": likelihood_of_attack,
            "typical_severity": typical_severity,
            "prerequisites": prerequisites,
            "indicators": indicators,
            "skills_required": skills_required,
            "resources_required": resources_required,
            "consequences": consequences,
            "mitigations": mitigations,
            "example_instances": example_instances,
            "alternate_terms": alternate_terms,
        }
        
        capec_instance, created = CAPEC.objects.update_or_create(id=capec_id, defaults=capec_data)
        capec_instances[capec_id] = capec_instance

        # Estrazione del flusso di esecuzione
        execution_flow_element = pattern.find('Execution_Flow')
        if execution_flow_element is not None:
            execution_flow_instance, _ = ExecutionFlow.objects.update_or_create(
                capec=capec_instance
            )
            # Aggiorna il campo execution_flow_instance di CAPEC
            capec_instance.execution_flow_instance = execution_flow_instance
            capec_instance.save()  # Salva le modifiche per associare l'ExecutionFlow al CAPEC

            # Dizionario per tenere traccia del conteggio dei duplicati per ciascun step_number
            step_counts = {}

            for attack_step in execution_flow_element.findall('Attack_Step'):
                # Pulizia e estrazione dei dettagli dello step
                step_number = clean_text(attack_step.find('Step').text)
                phase = clean_text(attack_step.find('Phase').text)
                description = extract_cleaned_text(attack_step.find('Description'))
                techniques = [extract_cleaned_text(tech) for tech in attack_step.findall('Technique')]

                # Incrementa il conteggio per lo step_number corrente
                if step_number in step_counts:
                    step_counts[step_number] += 1
                    # Aggiungi il suffisso alfabetico solo per i duplicati (a, b, c, ...)
                    suffixed_step_number = f"{step_number}{chr(96 + step_counts[step_number])}"  # 96 + 1 = 'a'
                else:
                    step_counts[step_number] = 1
                    # Usa solo il numero se è unico
                    suffixed_step_number = step_number

                # Aggiornamento o creazione dell'AttackStep con il numero modificato
                AttackStep.objects.update_or_create(
                    execution_flow=execution_flow_instance,
                    step=suffixed_step_number,
                    defaults={
                        "phase": phase,
                        "description": description,
                        "techniques": techniques,
                    }
                )

    # Gestione delle relazioni tra i pattern CAPEC
    for pattern in root.findall('.//Attack_Pattern'):
        capec_id = f"CAPEC-{pattern.get('ID')}"
        capec_instance = capec_instances.get(capec_id)
        
        for related_pattern in pattern.findall('Related_Attack_Patterns/Related_Attack_Pattern'):
            related_capec_id = f"CAPEC-{related_pattern.get('CAPEC_ID')}"
            nature = related_pattern.get("Nature")
            related_instance = capec_instances.get(related_capec_id)
            
            if capec_instance and related_instance:
                CAPECRelatedAttackPattern.objects.update_or_create(
                    source_capec=capec_instance,
                    target_capec=related_instance,
                    defaults={"nature": nature}
                )

    # Imposta il flag nel database
    print("Importazione CAPEC completata con successo.")
