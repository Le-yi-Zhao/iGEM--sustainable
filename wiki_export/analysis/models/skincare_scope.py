"""Endpoint selection by intended dermal use, before inspecting prediction values."""
CORE = ('AMES', 'Skin_Reaction', 'Carcinogens_Lagunin')
FORMULATION = ('Solubility_AqSolDB', 'Lipophilicity_AstraZeneca')
MECHANISTIC = ('NR-AR', 'NR-AR-LBD', 'NR-AhR', 'NR-Aromatase', 'NR-ER',
              'NR-ER-LBD', 'NR-PPAR-gamma', 'SR-ARE', 'SR-ATAD5',
              'SR-HSE', 'SR-MMP', 'SR-p53')
ACTIVE_AI = CORE + FORMULATION + MECHANISTIC
ATTRIBUTION_TASKS = CORE
MAPLIGHT_TASKS = ('ames',)
PRODUCT_ASSUMPTION = 'Provisional non-spray leave-on facial skincare; concentration and formulation not supplied'
GUIDANCE = 'https://health.ec.europa.eu/publications/sccs-notes-guidance-testing-cosmetic-ingredients-and-their-safety-evaluation-12th-revision_en'

def ai_scope(task):
    if task in CORE: return 'CORE_HAZARD'
    if task in FORMULATION: return 'FORMULATION_CONTEXT'
    if task in MECHANISTIC: return 'MECHANISTIC_FOLLOWUP'
    return 'NOT_IN_ROUTINE_SKINCARE_SCREEN'
