from django.contrib import admin
from data.models import CVE, CAPEC, CAPECRelatedAttackPattern, ExecutionFlow, AttackStep

# Register your models here.


### CVE Admin View

@admin.register(CVE)
class CVEAdmin(admin.ModelAdmin):
    list_display = ('id',  'description_short', 'published_date')
    search_fields = ('id', 'description')
    list_filter = ('published_date',)
    ordering = ('-published_date',)

    def description_short(self, obj):
        # Visualizza una versione breve della descrizione per una migliore leggibilità
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'

### CAPEC Admin View

class AttackStepInline(admin.TabularInline):
    model = AttackStep
    extra = 1  # Numero di moduli extra da mostrare

class ExecutionFlowAdmin(admin.ModelAdmin):
    inlines = [AttackStepInline]  # Aggiungi gli step come inline

class CAPECAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'execution_flow_instance')  # Visualizza anche l'Execution Flow
    search_fields = ('id', 'name')


admin.site.register(CAPEC, CAPECAdmin)
admin.site.register(ExecutionFlow, ExecutionFlowAdmin)
admin.site.register(CAPECRelatedAttackPattern)