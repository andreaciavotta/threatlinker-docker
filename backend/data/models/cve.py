from django.db import models
from django.db.models import JSONField

class CVE(models.Model):
    id = models.CharField(max_length=20, primary_key=True)

    # Descrizione e Date
    description = models.TextField()
    published_date = models.DateTimeField()

    # Impatto
    impact_v2 = JSONField(null=True, blank=True)
    impact_v3 = JSONField(null=True, blank=True)

    def get_summary(self):
        return self.description[:100] + '...' if len(self.description) > 100 else self.description

    def __str__(self):
        return self.id
    
    def get_vector_string(self):
        return self.impact_v2.get('vectorString', 'N/A')

    def get_attack_vector(self):
        return self.impact_v2.get('cvssV2', {}).get('accessVector', 'N/A')

    def get_access_complexity(self):
        return self.impact_v2.get('cvssV2', {}).get('accessComplexity', 'N/A')

    def get_authentication(self):
        return self.impact_v2.get('cvssV2', {}).get('authentication', 'N/A')

    def get_confidentiality_impact(self):
        return self.impact_v2.get('cvssV2', {}).get('confidentialityImpact', 'N/A')

    def get_integrity_impact(self):
        return self.impact_v2.get('cvssV2', {}).get('integrityImpact', 'N/A')

    def get_availability_impact(self):
        return self.impact_v2.get('cvssV2', {}).get('availabilityImpact', 'N/A')

    def get_base_score(self):
        return self.impact_v2.get('cvssV2', {}).get('baseScore', 'N/A')

    # Funzioni per gli impatti V3

    def get_vector_string_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('vectorString', 'No vector string available.')
        return 'Impact V3 data is not available.'

    def get_attack_vector_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('attackVector', 'No attack vector available.')
        return 'Impact V3 data is not available.'

    def get_attack_complexity_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('attackComplexity', 'No attack complexity available.')
        return 'Impact V3 data is not available.'

    def get_privileges_required_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('privilegesRequired', 'No privileges required information available.')
        return 'Impact V3 data is not available.'

    def get_user_interaction_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('userInteraction', 'No user interaction information available.')
        return 'Impact V3 data is not available.'

    def get_confidentiality_impact_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('confidentialityImpact', 'No confidentiality impact information available.')
        return 'Impact V3 data is not available.'

    def get_integrity_impact_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('integrityImpact', 'No integrity impact information available.')
        return 'Impact V3 data is not available.'

    def get_availability_impact_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('availabilityImpact', 'No availability impact information available.')
        return 'Impact V3 data is not available.'

    def get_base_score_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('baseScore', 'No base score available.')
        return 'Impact V3 data is not available.'

    def get_base_severity_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('baseSeverity', 'No base severity information available.')
        return 'Impact V3 data is not available.'

    def get_scope_v3(self):
        if self.impact_v3 and 'cvssV3' in self.impact_v3:
            return self.impact_v3['cvssV3'].get('scope', 'No scope information available.')
        return 'Impact V3 data is not available.'
    

    
