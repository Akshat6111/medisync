"""
Curated reference list of ~350 commonly prescribed generic and brand drug names.
Used by RxParse for fuzzy string matching with RapidFuzz to resolve OCR misreadings.
"""

COMMON_DRUG_NAMES = [
    # Cardiovascular & Blood Pressure
    "Amlodipine", "Telmisartan", "Losartan", "Ramipril", "Enalapril",
    "Lisinopril", "Atenolol", "Metoprolol", "Bisoprolol", "Carvedilol",
    "Nebivolol", "Hydrochlorothiazide", "Chlorthalidone", "Furosemide",
    "Torsemide", "Spironolactone", "Diltiazem", "Verapamil", "Clonidine",
    "Prazosin", "Hydralazine", "Nitroglycerin", "Isosorbide Mononitrate",
    "Digoxin", "Ivabradine", "Sacubitril", "Valsartan", "Olmesartan",
    "Candesartan", "Perindopril",

    # Statins & Lipid Lowering
    "Atorvastatin", "Rosuvastatin", "Simvastatin", "Pravastatin",
    "Fenofibrate", "Ezetimibe", "Gemfibrozil",

    # Antiplatelet & Anticoagulant
    "Aspirin", "Clopidogrel", "Ticagrelor", "Prasugrel", "Warfarin",
    "Rivaroxaban", "Apixaban", "Dabigatran", "Heparin",

    # Diabetes
    "Metformin", "Glimepiride", "Gliclazide", "Glipizide", "Sitagliptin",
    "Vildagliptin", "Teneligliptin", "Linagliptin", "Empagliflozin",
    "Dapagliflozin", "Canagliflozin", "Pioglitazone", "Acarbose",
    "Voglibose", "Semaglutide", "Dulaglutide", "Liraglutide",
    "Insulin Glargine", "Insulin Aspart", "Insulin Lispro",

    # Antibiotics & Antimicrobials
    "Amoxicillin", "Augmentin", "Amoxyclav", "Amoxicillin and Clavulanate", "Azithromycin",
    "Ciprofloxacin", "Levofloxacin", "Ofloxacin", "Norfloxacin",
    "Cefixime", "Ceftriaxone", "Cefuroxime", "Cefpodoxime", "Cephalexin",
    "Cefazolin", "Doxycycline", "Metronidazole", "Clarithromycin",
    "Erythromycin", "Nitrofurantoin", "Trimethoprim", "Sulfamethoxazole",
    "Co-Trimoxazole", "Linezolid", "Meropenem", "Vancomycin",
    "Piperacillin", "Tazobactam", "Gentamicin", "Amikacin",

    # Antifungal & Antiviral
    "Fluconazole", "Itraconazole", "Voriconazole", "Ketoconazole",
    "Terbinafine", "Acyclovir", "Valacyclovir", "Oseltamivir", "Remdesivir",

    # Analgesics & Anti-inflammatory (NSAIDs)
    "Paracetamol", "Acetaminophen", "Ibuprofen", "Diclofenac", "Aceclofenac",
    "Naproxen", "Tramadol", "Ketorolac", "Meloxicam", "Celecoxib",
    "Etoricoxib", "Mefenamic Acid", "Piroxicam", "Indomethacin",

    # Gastrointestinal
    "Pantoprazole", "Omeprazole", "Rabeprazole", "Esomeprazole",
    "Lansoprazole", "Ranitidine", "Famotidine", "Domperidone",
    "Ondansetron", "Metoclopramide", "Sucralfate", "Lactulose",
    "Loperamide", "Mesalamine", "Sulfasalazine", "Ursodeoxycholic Acid",
    "Hyoscine", "Dicyclomine",

    # Respiratory, Antiallergic & Asthma
    "Cetirizine", "Levocetirizine", "Montelukast", "Loratadine",
    "Desloratadine", "Fexofenadine", "Bilastine", "Salbutamol",
    "Albuterol", "Budesonide", "Fluticasone", "Formoterol",
    "Ipratropium", "Tiotropium", "Acebrophylline", "Theophylline",
    "Dextromethorphan", "Ambroxol", "Guaifenesin", "Acetylcysteine",

    # Steroids & Hormones
    "Prednisolone", "Methylprednisolone", "Dexamethasone", "Hydrocortisone",
    "Betamethasone", "Levothyroxine", "Carbimazole", "Methimazole",
    "Progesterone", "Medroxyprogesterone", "Estradiol", "Testosterone",

    # Neurology & Psychiatry
    "Gabapentin", "Pregabalin", "Levetiracetam", "Sodium Valproate",
    "Carbamazepine", "Phenytoin", "Lamotrigine", "Topiramate",
    "Escitalopram", "Sertraline", "Fluoxetine", "Paroxetine",
    "Duloxetine", "Venlafaxine", "Amitriptyline", "Nortriptyline",
    "Clonazepam", "Alprazolam", "Diazepam", "Lorazepam", "Zolpidem",
    "Quetiapine", "Olanzapine", "Risperidone", "Aripiprazole",
    "Haloperidol", "Baclofen", "Tizanidine",

    # Vitamins, Minerals & Supplements
    "Calcium Carbonate", "Cholecalciferol", "Vitamin D3", "Vitamin C",
    "Ascorbic Acid", "Folic Acid", "Ferrous Ascorbate", "Ferrous Sulfate",
    "Methylcobalamin", "Cyanocobalamin", "Zinc Sulfate", "Multivitamin",
    "Omega 3", "Coenzyme Q10",

    # Urological & Miscellaneous
    "Tamsulosin", "Finasteride", "Silodosin", "Alfuzosin",
    "Allopurinol", "Febuxostat", "Colchicine", "Methotrexate",
    "Hydroxychloroquine", "Azathioprine",

    # Popular Indian Brand Names & Formulations
    "Pan", "Pan 40", "Pan D", "Pantocid", "Razo", "Omez", "Aciloc",
    "Switch CV", "Switch", "Cefpodoxime and Clavulanic Acid",
    "Vizylac", "Vizylac Rich", "Probiotics", "Sporlac", "Darolac",
    "Meftal Forte", "Meftal", "Mefenamic Acid and Paracetamol",
    "Ebast M", "Ebast", "Ebastine and Montelukast",
    "Mucaryl", "Mucinac", "Fluimucil", "N-Acetylcysteine",
    "Influvac", "Influenza Vaccine",
    "Dolo", "Dolo 650", "Calpol", "Crocin", "Combiflam", "Flexon",
    "Allegra", "Montek LC", "Montair LC", "Telekast", "Levocet",
    "Augmentin", "Amoxyclav", "Moxikind CV", "Clavam",
    "Azithral", "Azee", "Zady", "Zifi", "Taxim O", "Monocef", "Mahacef",
    "O2", "Oflox", "Ciplox", "Norflox", "Cifran",
    "Shelcal", "Becosules", "Limcee", "Celin", "Neurobion", "Evion",
    "Glycomet", "Januvia", "Galvus", "Jardiance", "Forxiga", "Teniva",
    "Thyronorm", "Eltroxin", "Asthalin", "Deriphyllin", "Duolin", "Budecort",
]
