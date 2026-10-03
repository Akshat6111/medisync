"""
Curated static mapping of brand names, active salt / generic chemical compositions,
and Indian generic substitutes.
Used by GenericFinder for fuzzy-matching user queries, identifying equivalent formulations,
and benchmarking savings against Pradhan Mantri Bhartiya Janaushadhi Pariyojana (PMBJP).
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process

SALT_DICTIONARY: Dict[str, Dict[str, Any]] = {
    # ----------------------------------------------------
    # 1. Analgesics, Antipyretics & Pain Relief
    # ----------------------------------------------------
    "Paracetamol": {
        "generic_name": "Paracetamol",
        "category": "Pain & Fever",
        "description": "Widely used for mild-to-moderate fever, headache, body ache, and flu symptoms.",
        "common_strengths": ["500mg", "650mg"],
        "pmbjp_price": 9.50,
        "market_avg_price": 32.00,
        "how_to_use": "Take with water after meals. Do not exceed 4000mg per day to avoid liver strain.",
        "side_effects": ["Nausea", "Mild allergic skin rash (rare)"],
        "brands": [
            "Dolo 650",
            "Calpol 650",
            "Crocin 650",
            "Pacimol 650",
            "Pyrigesic 650",
            "Sumo L 650",
            "P-650",
            "T-98 650",
            "Paracip 650",
            "Fepanil 650",
        ],
    },
    "Ibuprofen": {
        "generic_name": "Ibuprofen",
        "category": "Pain & Fever",
        "description": "Non-steroidal anti-inflammatory drug used for toothache, backache, and arthritis.",
        "common_strengths": ["200mg", "400mg"],
        "pmbjp_price": 8.00,
        "market_avg_price": 28.00,
        "how_to_use": "Always take after food to prevent stomach acidity and mucosal ulceration.",
        "side_effects": ["Stomach irritation", "Heartburn", "Dizziness"],
        "brands": ["Brufen 400", "Ibugesic 400", "Ibupal 400", "Advil 200", "Flamar 400"],
    },
    "Ibuprofen + Paracetamol": {
        "generic_name": "Ibuprofen + Paracetamol",
        "category": "Pain & Fever",
        "description": "Synergistic dual-action combination for fever, toothache, muscular pain, and headache.",
        "common_strengths": ["400mg + 325mg"],
        "pmbjp_price": 11.00,
        "market_avg_price": 42.00,
        "how_to_use": "Take one tablet post-meal with a full glass of water. Avoid taking on empty stomach.",
        "side_effects": ["Gastric discomfort", "Nausea", "Heartburn"],
        "brands": ["Combiflam", "Flexon", "Ibugesic Plus", "Brufen Plus", "Zupar"],
    },
    "Aceclofenac + Paracetamol": {
        "generic_name": "Aceclofenac + Paracetamol",
        "category": "Pain & Fever",
        "description": "Standard Indian prescription formulation for acute musculoskeletal pain and joint swelling.",
        "common_strengths": ["100mg + 325mg"],
        "pmbjp_price": 14.00,
        "market_avg_price": 68.00,
        "how_to_use": "Take after meals. Avoid combining with other pain killers or alcohol.",
        "side_effects": ["Indigestion", "Drowsiness", "Mild stomach pain"],
        "brands": ["Zerodol-P", "Hifenac-P", "Dolokind-P", "Aceclo-Plus", "Movace-P", "Arflur-P"],
    },
    "Aceclofenac + Paracetamol + Serratiopeptidase": {
        "generic_name": "Aceclofenac + Paracetamol + Serratiopeptidase",
        "category": "Pain & Fever",
        "description": "Prescribed for postoperative pain, trauma, dental extraction, and heavy tissue edema.",
        "common_strengths": ["100mg + 325mg + 15mg"],
        "pmbjp_price": 24.00,
        "market_avg_price": 115.00,
        "how_to_use": "Take strictly after meals for anti-inflammatory tissue recovery and wound edema relief.",
        "side_effects": ["Mild nausea", "Diarrhea", "Dizziness"],
        "brands": ["Zerodol-SP", "Hifenac-SP", "Dolokind-SP", "Signoflam", "Aldigesic-SP", "Flozen-AA"],
    },
    "Diclofenac Sodium": {
        "generic_name": "Diclofenac Sodium",
        "category": "Pain & Fever",
        "description": "Potent pain and inflammation manager used in arthritis, sprains, and back pain.",
        "common_strengths": ["50mg", "75mg"],
        "pmbjp_price": 7.50,
        "market_avg_price": 35.00,
        "how_to_use": "Take with meals or milk to minimize gastric upset.",
        "side_effects": ["Nausea", "Heartburn", "Stomach ache"],
        "brands": ["Voveran 50", "Dynapar EC", "Dicloran 50", "Jonac 50", "Volini Tablet"],
    },
    "Mefenamic Acid + Paracetamol": {
        "generic_name": "Mefenamic Acid + Paracetamol",
        "category": "Pain & Fever",
        "description": "Popular medicine for menstrual cramps, abdominal pain, and pediatric fever.",
        "common_strengths": ["250mg + 325mg", "500mg + 325mg"],
        "pmbjp_price": 12.00,
        "market_avg_price": 52.00,
        "how_to_use": "Take with food during active spasmodic or menstrual pain episodes.",
        "side_effects": ["Abdominal cramps", "Heartburn", "Mild dizziness"],
        "brands": ["Meftal Forte", "Meftal-P", "Mefkind-Forte", "Centamol Plus", "Mefanorm Plus"],
    },
    "Etoricoxib": {
        "generic_name": "Etoricoxib",
        "category": "Pain & Fever",
        "description": "Relieves severe joint pain and inflammation in osteoarthritis, gout, and ankylosing spondylitis.",
        "common_strengths": ["60mg", "90mg", "120mg"],
        "pmbjp_price": 28.00,
        "market_avg_price": 135.00,
        "how_to_use": "Take once daily with or without food at the same time each day.",
        "side_effects": ["Fluid retention", "Mild headache", "Elevated blood pressure"],
        "brands": ["Nucoxia 90", "Arcoxia 90", "Etoshine 90", "Etody 90", "Etrobax 90"],
    },
    "Tramadol + Paracetamol": {
        "generic_name": "Tramadol + Paracetamol",
        "category": "Pain & Fever",
        "description": "Prescription pain medication for moderate-to-severe surgical and chronic pain.",
        "common_strengths": ["37.5mg + 325mg"],
        "pmbjp_price": 20.00,
        "market_avg_price": 95.00,
        "how_to_use": "Strictly follow prescription dose. Avoid operating machinery or driving.",
        "side_effects": ["Drowsiness", "Nausea", "Constipation", "Dizziness"],
        "brands": ["Ultracet", "Tramazac-P", "Dolzero", "Calpol-T", "Urgendol-P"],
    },

    # ----------------------------------------------------
    # 2. Antibiotics & Antimicrobials
    # ----------------------------------------------------
    "Amoxicillin + Clavulanic Acid": {
        "generic_name": "Amoxicillin + Clavulanic Acid",
        "category": "Antibiotics",
        "description": "Antibiotic with beta-lactamase inhibitor for respiratory, sinus, dental, skin, and ear infections.",
        "common_strengths": ["625mg"],
        "pmbjp_price": 54.00,
        "market_avg_price": 210.00,
        "how_to_use": "Take at the start of a meal to minimize GI upset. Complete the full prescribed course.",
        "side_effects": ["Diarrhea", "Nausea", "Vomiting", "Mild skin rash"],
        "brands": [
            "Augmentin 625 Duo",
            "Moxikind-CV 625",
            "Clavam 625",
            "Amoxyclav 625",
            "Sensiclav 625",
            "Mega-CV 625",
            "Polyclav 625",
            "Novamox CV 625",
        ],
    },
    "Azithromycin": {
        "generic_name": "Azithromycin",
        "category": "Antibiotics",
        "description": "Once-daily antibiotic for chest infections, sore throat, tonsillitis, typhoid, and skin infections.",
        "common_strengths": ["250mg", "500mg"],
        "pmbjp_price": 38.00,
        "market_avg_price": 125.00,
        "how_to_use": "Take once daily 1 hour before or 2 hours after a meal with plenty of water.",
        "side_effects": ["Stomach cramps", "Loose stools", "Headache"],
        "brands": ["Azithral 500", "Azee 500", "Zady 500", "Zithrox 500", "ATM 500", "Azimax 500"],
    },
    "Cefixime": {
        "generic_name": "Cefixime",
        "category": "Antibiotics",
        "description": "Oral cephalosporin used for urinary tract, ENT, and uncomplicated typhoid infections.",
        "common_strengths": ["100mg", "200mg"],
        "pmbjp_price": 36.00,
        "market_avg_price": 118.00,
        "how_to_use": "Take with or without food. Complete the full antibiotic cycle.",
        "side_effects": ["Mild diarrhea", "Dyspepsia", "Abdominal discomfort"],
        "brands": ["Zifi 200", "Taxim-O 200", "Mahacef 200", "Cefolac 200", "Omnicef-O 200", "Ziprax 200"],
    },
    "Cefpodoxime Proxetil": {
        "generic_name": "Cefpodoxime Proxetil",
        "category": "Antibiotics",
        "description": "Antibiotic used for acute bronchitis, pneumonia, and severe sinusitis.",
        "common_strengths": ["100mg", "200mg"],
        "pmbjp_price": 58.00,
        "market_avg_price": 175.00,
        "how_to_use": "Take with food to enhance gastrointestinal absorption.",
        "side_effects": ["Nausea", "Abdominal discomfort", "Headache"],
        "brands": ["Gudcef 200", "Doxcef 200", "Monocef-O 200", "Macpod 200", "Cepodem 200", "Switch 200"],
    },
    "Cefuroxime Axetil": {
        "generic_name": "Cefuroxime Axetil",
        "category": "Antibiotics",
        "description": "Broad-spectrum coverage for bone, joint, soft tissue, and respiratory tract infections.",
        "common_strengths": ["250mg", "500mg"],
        "pmbjp_price": 90.00,
        "market_avg_price": 430.00,
        "how_to_use": "Take with food for optimal bioavailability and therapeutic effect.",
        "side_effects": ["Headache", "Gastrointestinal upset", "Dizziness"],
        "brands": ["Ceftum 500", "Ceroxim 500", "Cetil 500", "Forcef 500", "Zefu 500", "Pulmocef 500"],
    },
    "Ciprofloxacin": {
        "generic_name": "Ciprofloxacin",
        "category": "Antibiotics",
        "description": "Used for bacterial diarrhea, bone infections, complicated UTIs, and abdominal sepsis.",
        "common_strengths": ["250mg", "500mg"],
        "pmbjp_price": 16.00,
        "market_avg_price": 48.00,
        "how_to_use": "Take with water. Avoid antacids, dairy, or calcium supplements 2 hours before or after.",
        "side_effects": ["Nausea", "Tendon sensitivity", "Mild dizziness"],
        "brands": ["Ciplox 500", "Cifran 500", "Ciprobid 500", "Quintor 500", "Alcipro 500"],
    },
    "Ofloxacin + Ornidazole": {
        "generic_name": "Ofloxacin + Ornidazole",
        "category": "Antibiotics",
        "description": "Standard therapy in India for mixed gastrointestinal bacterial and protozoal infections (loose motions).",
        "common_strengths": ["200mg + 500mg"],
        "pmbjp_price": 22.00,
        "market_avg_price": 85.00,
        "how_to_use": "Take after meals twice daily. Stay hydrated with electrolytes.",
        "side_effects": ["Metallic taste", "Loss of appetite", "Nausea"],
        "brands": ["O2 Tablet", "Zenflox-OZ", "Zanocin-OZ", "Ornof 200/500", "Oflomac-OZ"],
    },
    "Doxycycline": {
        "generic_name": "Doxycycline",
        "category": "Antibiotics",
        "description": "Used for acne vulgaris, rickettsial fever, cholera, malaria prophylaxis, and respiratory infections.",
        "common_strengths": ["100mg"],
        "pmbjp_price": 14.00,
        "market_avg_price": 45.00,
        "how_to_use": "Take with a full glass of water while sitting upright. Do not lie down for 30 minutes.",
        "side_effects": ["Sun sensitivity", "Stomach irritation", "Nausea"],
        "brands": ["Doxicip 100", "Doxy-1 L-DR", "Microdox-LBX", "Minicycline 100", "Doxt-SL"],
    },
    "Metronidazole": {
        "generic_name": "Metronidazole",
        "category": "Antibiotics",
        "description": "Treats amoebiasis, dental abscess, pelvic inflammatory disease, and anaerobic bacteria.",
        "common_strengths": ["200mg", "400mg"],
        "pmbjp_price": 6.50,
        "market_avg_price": 24.00,
        "how_to_use": "Strictly avoid alcohol during treatment and for at least 48 hours after stopping.",
        "side_effects": ["Metallic taste", "Darkened urine", "Headache"],
        "brands": ["Flagyl 400", "Metrogyl 400", "Aristogyl 400", "Aldezole 400"],
    },

    # ----------------------------------------------------
    # 3. Antacids, Acid Reflux & Gastrointestinal (GI)
    # ----------------------------------------------------
    "Pantoprazole": {
        "generic_name": "Pantoprazole",
        "category": "Acidity & Digestion",
        "description": "Suppresses stomach acid secretion; treats GERD, peptic ulcers, and hyperacidity.",
        "common_strengths": ["40mg"],
        "pmbjp_price": 18.00,
        "market_avg_price": 155.00,
        "how_to_use": "Take in the morning 30-60 minutes before breakfast with a glass of water.",
        "side_effects": ["Headache", "Flatulence", "Diarrhea"],
        "brands": ["Pan 40", "Pantocid 40", "Pantodac 40", "Pantop 40", "Pantocar 40", "Nupenta 40"],
    },
    "Pantoprazole + Domperidone": {
        "generic_name": "Pantoprazole + Domperidone",
        "category": "Acidity & Digestion",
        "description": "Combination for GERD accompanied by nausea, vomiting, fullness, and bloating.",
        "common_strengths": ["40mg + 30mg SR"],
        "pmbjp_price": 28.00,
        "market_avg_price": 210.00,
        "how_to_use": "Take on an empty stomach 30 minutes before the first meal of the day.",
        "side_effects": ["Dry mouth", "Mild headache", "Diarrhea"],
        "brands": ["Pan-D", "Pantocid-D SR", "Dompan SR", "Pantocar-D", "Nupenta-D", "Pantakind-D"],
    },
    "Omeprazole": {
        "generic_name": "Omeprazole",
        "category": "Acidity & Digestion",
        "description": "First-generation PPI for heartburn, gastroesophageal reflux, and acid indigestion.",
        "common_strengths": ["20mg"],
        "pmbjp_price": 12.00,
        "market_avg_price": 62.00,
        "how_to_use": "Take on an empty stomach before morning tea or breakfast.",
        "side_effects": ["Abdominal pain", "Nausea", "Headache"],
        "brands": ["Omez 20", "Omee 20", "Lokit 20", "Ocid 20", "Omecip 20"],
    },
    "Rabeprazole": {
        "generic_name": "Rabeprazole",
        "category": "Acidity & Digestion",
        "description": "Fast-acting proton pump inhibitor providing rapid relief from acid reflux and heartburn.",
        "common_strengths": ["20mg"],
        "pmbjp_price": 20.00,
        "market_avg_price": 140.00,
        "how_to_use": "Take in early morning before breakfast.",
        "side_effects": ["Headache", "Sore throat", "Constipation"],
        "brands": ["Razo 20", "Happi 20", "Rabicip 20", "Veloz 20", "Rablet 20", "Cyra 20"],
    },
    "Rabeprazole + Domperidone": {
        "generic_name": "Rabeprazole + Domperidone",
        "category": "Acidity & Digestion",
        "description": "Dual treatment for acid regurgitation, nausea, indigestion, and gastroparesis.",
        "common_strengths": ["20mg + 30mg SR"],
        "pmbjp_price": 32.00,
        "market_avg_price": 235.00,
        "how_to_use": "Take 30 minutes before your morning meal.",
        "side_effects": ["Dry mouth", "Dizziness", "Abdominal discomfort"],
        "brands": ["Razo-D", "Happi-D", "Cyra-D", "Rabicip-D", "Veloz-D", "Rablet-D"],
    },
    "Esomeprazole": {
        "generic_name": "Esomeprazole",
        "category": "Acidity & Digestion",
        "description": "S-isomer of omeprazole with prolonged intragastric acid suppression.",
        "common_strengths": ["20mg", "40mg"],
        "pmbjp_price": 25.00,
        "market_avg_price": 165.00,
        "how_to_use": "Take at least 1 hour before food.",
        "side_effects": ["Headache", "Nausea", "Flatulence"],
        "brands": ["Nexpro 40", "Sompraz 40", "Esomac 40", "Raciper 40", "Izra 40"],
    },
    "Ranitidine": {
        "generic_name": "Ranitidine",
        "category": "Acidity & Digestion",
        "description": "Traditional acid reducer for sour stomach and ulcer prevention.",
        "common_strengths": ["150mg", "300mg"],
        "pmbjp_price": 7.00,
        "market_avg_price": 42.00,
        "how_to_use": "Take before meals or at bedtime.",
        "side_effects": ["Constipation", "Drowsiness"],
        "brands": ["Aciloc 150", "Rantac 150", "Zinetac 150", "Histac 150"],
    },
    "Ondansetron": {
        "generic_name": "Ondansetron",
        "category": "Acidity & Digestion",
        "description": "Prevents and treats nausea and vomiting caused by chemotherapy, radiation, or stomach bugs.",
        "common_strengths": ["4mg", "8mg"],
        "pmbjp_price": 8.50,
        "market_avg_price": 45.00,
        "how_to_use": "Take 30 minutes before food or prior to medical procedures.",
        "side_effects": ["Constipation", "Headache", "Warm feeling"],
        "brands": ["Emeset 4", "Ondem 4", "Vomikind 4", "Zofran 4", "Periset 4"],
    },
    "Loperamide": {
        "generic_name": "Loperamide",
        "category": "Acidity & Digestion",
        "description": "Slows intestinal peristalsis to control sudden acute non-infectious diarrhea.",
        "common_strengths": ["2mg"],
        "pmbjp_price": 4.50,
        "market_avg_price": 22.00,
        "how_to_use": "Take after the first loose stool; drink plenty of oral rehydration solution (ORS).",
        "side_effects": ["Constipation", "Dizziness", "Tiredness"],
        "brands": ["Imodium 2", "Eldoper 2", "Lopamide 2", "Roko 2", "Lopram 2"],
    },

    # ----------------------------------------------------
    # 4. Antihistamines, Respiratory & Allergy
    # ----------------------------------------------------
    "Cetirizine": {
        "generic_name": "Cetirizine",
        "category": "Allergy & Cough",
        "description": "Relieves allergic rhinitis, runny nose, sneezing, itchy eyes, and hives.",
        "common_strengths": ["10mg"],
        "pmbjp_price": 5.50,
        "market_avg_price": 22.00,
        "how_to_use": "Take in the evening or at night. May cause mild drowsiness in sensitive individuals.",
        "side_effects": ["Drowsiness", "Dry mouth", "Fatigue"],
        "brands": ["Cetzine 10", "Alerid 10", "Zyrtec 10", "Okacet 10", "Incid-L 10"],
    },
    "Levocetirizine": {
        "generic_name": "Levocetirizine",
        "category": "Allergy & Cough",
        "description": "Active enantiomer of cetirizine with lower drowsiness for seasonal allergies.",
        "common_strengths": ["5mg"],
        "pmbjp_price": 9.00,
        "market_avg_price": 48.00,
        "how_to_use": "Take once daily in the evening with or without food.",
        "side_effects": ["Mild tiredness", "Dry mouth"],
        "brands": ["Levocet 5", "1-AL 5", "Teczine 5", "Vozet 5", "L-Hist 5", "Xyzal 5"],
    },
    "Levocetirizine + Montelukast": {
        "generic_name": "Levocetirizine + Montelukast",
        "category": "Allergy & Cough",
        "description": "Leading combination in India for allergic asthma, allergic bronchitis, and dust allergy.",
        "common_strengths": ["5mg + 10mg"],
        "pmbjp_price": 32.00,
        "market_avg_price": 185.00,
        "how_to_use": "Take once daily at bedtime for optimal asthma and nighttime allergy control.",
        "default_form": "tablet",
        "brands": [
            {"name": "Montecip LC", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Montair LC", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Montek LC", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Montiwor-LC", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Telekast-L", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Levocet-M", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Romilast-L", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Phensedyl LM", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Monticope", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Odimont-LC", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Lasma LC", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Montas-L", "form": "tablet", "strength": "5mg + 10mg"},
            {"name": "Minolast-LC", "form": "tablet", "strength": "5mg + 10mg"},
            # Pediatric / Syrups (different dosage form)
            {"name": "Relikast-LC Kid Syrup", "form": "syrup", "strength": "2.5mg + 4mg / 5ml"},
            {"name": "Montair LC Kid Syrup", "form": "syrup", "strength": "2.5mg + 4mg / 5ml"},
            {"name": "Montecip LC Junior Syrup", "form": "syrup", "strength": "2.5mg + 4mg / 5ml"},
            {"name": "Montor-LC Kid Syrup", "form": "syrup", "strength": "2.5mg + 4mg / 5ml"},
        ],
    },
    "Fexofenadine": {
        "generic_name": "Fexofenadine",
        "category": "Allergy & Cough",
        "description": "Completely non-drowsy antihistamine for chronic urticaria, allergies, and hay fever.",
        "common_strengths": ["120mg", "180mg"],
        "pmbjp_price": 35.00,
        "market_avg_price": 215.00,
        "how_to_use": "Take with water. Avoid fruit juices 4 hours before and after consumption.",
        "side_effects": ["Headache", "Drowsiness (rare)", "Nausea"],
        "brands": ["Allegra 120", "Allegra 180", "Fexova 120", "Histafree 120", "Fexy 120", "Alertin 120"],
    },
    "Bilastine": {
        "generic_name": "Bilastine",
        "category": "Allergy & Cough",
        "description": "Next-generation antihistamine without cardiac or sedative side effects.",
        "common_strengths": ["20mg"],
        "pmbjp_price": 45.00,
        "market_avg_price": 180.00,
        "how_to_use": "Must be taken 1 hour before or 2 hours after food or fruit juices.",
        "side_effects": ["Headache", "Dizziness"],
        "brands": ["Bilasave 20", "Bilachek 20", "Bilaxten 20", "Bilashine 20", "Bilast 20"],
    },
    "Ambroxol + Levosalbutamol + Guaifenesin": {
        "generic_name": "Ambroxol + Levosalbutamol + Guaifenesin",
        "category": "Allergy & Cough",
        "description": "Clears thick mucus and widens bronchial airways in productive chesty cough.",
        "common_strengths": ["Syrup 100ml"],
        "pmbjp_price": 28.00,
        "market_avg_price": 118.00,
        "how_to_use": "Shake well before use. Drink plenty of warm fluids to help loosen phlegm.",
        "side_effects": ["Fine tremors", "Palpitations", "Nausea"],
        "brands": ["Ascoril LS Syrup", "Solvin LS Syrup", "Bro-Zedex LS", "Mucolite LS", "Cheston LS"],
    },
    "Dextromethorphan + Chlorpheniramine": {
        "generic_name": "Dextromethorphan + Chlorpheniramine",
        "category": "Allergy & Cough",
        "description": "Calms cough reflex in throat and suppresses persistent dry tickly coughing.",
        "common_strengths": ["Syrup 100ml"],
        "pmbjp_price": 24.00,
        "market_avg_price": 105.00,
        "how_to_use": "Take as prescribed. Avoid driving if feeling sleepy.",
        "default_form": "syrup",
        "brands": [
            {"name": "Phensedyl DX Syrup", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
            {"name": "Phensedyl Cough Syrup", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
            {"name": "Phensedyl", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
            {"name": "Benadryl DR", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
            {"name": "Ascoril D Plus", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
            {"name": "Chericof Syrup", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
            {"name": "TusQ-DX", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
            {"name": "Zedex DX", "form": "syrup", "strength": "10mg + 2mg / 5ml"},
        ],
    },

    # ----------------------------------------------------
    # 5. Diabetes Management
    # ----------------------------------------------------
    "Metformin": {
        "generic_name": "Metformin",
        "category": "Diabetes",
        "description": "First-line oral antidiabetic medicine for Type 2 Diabetes; reduces hepatic glucose production.",
        "common_strengths": ["500mg", "850mg", "1000mg"],
        "pmbjp_price": 8.50,
        "market_avg_price": 45.00,
        "how_to_use": "Take with or right after meals to avoid gastrointestinal upset and nausea.",
        "side_effects": ["Nausea", "Metallic taste", "Stomach cramps"],
        "brands": ["Glycomet 500", "Glyciphage 500", "Obimet 500", "Cetapin 500", "Formin 500", "Metsmall 500"],
    },
    "Glimepiride": {
        "generic_name": "Glimepiride",
        "category": "Diabetes",
        "description": "Stimulates pancreatic beta cells to produce more natural insulin.",
        "common_strengths": ["1mg", "2mg", "3mg"],
        "pmbjp_price": 7.50,
        "market_avg_price": 65.00,
        "how_to_use": "Take just before or with your first main meal of the day.",
        "side_effects": ["Hypoglycemia (low blood sugar)", "Dizziness", "Weakness"],
        "brands": ["Amaryl 1mg", "Amaryl 2mg", "Glimestar 2", "GP 2", "Zoryl 2", "Euglim 2"],
    },
    "Glimepiride + Metformin": {
        "generic_name": "Glimepiride + Metformin",
        "category": "Diabetes",
        "description": "Most widely prescribed combination therapy for Indian Type 2 diabetic patients.",
        "common_strengths": ["1mg + 500mg", "2mg + 500mg"],
        "pmbjp_price": 15.00,
        "market_avg_price": 110.00,
        "how_to_use": "Take with breakfast. Always carry glucose or sweets in case of low blood sugar.",
        "side_effects": ["Hypoglycemia", "Nausea", "Diarrhea"],
        "brands": ["Glycomet-GP 1", "Glycomet-GP 2", "Amaryl M 2", "Glimisave M 2", "Zoryl M 2", "GP 2 Forte"],
    },
    "Vildagliptin": {
        "generic_name": "Vildagliptin",
        "category": "Diabetes",
        "description": "Increases incretin hormones to regulate post-prandial blood sugar spikes with low hypoglycemia risk.",
        "common_strengths": ["50mg"],
        "pmbjp_price": 32.00,
        "market_avg_price": 145.00,
        "how_to_use": "Take twice daily in morning and evening with or without food.",
        "side_effects": ["Tremors", "Headache", "Mild hypoglycemia"],
        "brands": ["Galvus 50", "Jalra 50", "Vysov 50", "Zomelis 50", "Vilano 50"],
    },
    "Sitagliptin": {
        "generic_name": "Sitagliptin",
        "category": "Diabetes",
        "description": "Once-daily dipeptidyl peptidase-4 inhibitor for glycaemic control.",
        "common_strengths": ["50mg", "100mg"],
        "pmbjp_price": 42.00,
        "market_avg_price": 360.00,
        "how_to_use": "Take once daily anytime with or without food.",
        "side_effects": ["Upper respiratory tract infection", "Headache"],
        "brands": ["Januvia 100", "Istavel 100", "Zita 100", "Sitagress 100"],
    },
    "Teneligliptin": {
        "generic_name": "Teneligliptin",
        "category": "Diabetes",
        "description": "Cost-effective gliptin therapy designed specifically for South Asian diabetic demographics.",
        "common_strengths": ["20mg"],
        "pmbjp_price": 18.00,
        "market_avg_price": 95.00,
        "how_to_use": "Take once daily before or after breakfast.",
        "side_effects": ["Hypoglycemia", "Constipation", "Dizziness"],
        "brands": ["Teniva 20", "Tenglyn 20", "Ziten 20", "Tenepure 20", "Inogla 20"],
    },
    "Dapagliflozin": {
        "generic_name": "Dapagliflozin",
        "category": "Diabetes",
        "description": "Expels excess blood glucose through urine; provides heart failure and kidney protective benefits.",
        "common_strengths": ["5mg", "10mg"],
        "pmbjp_price": 38.00,
        "market_avg_price": 215.00,
        "how_to_use": "Take once daily in the morning. Drink plenty of water throughout the day.",
        "side_effects": ["Genital mycotic infections", "Increased urination", "Dehydration"],
        "brands": ["Forxiga 10", "Oxra 10", "Dapaone 10", "Dapaglyn 10", "Justo 10"],
    },
    "Empagliflozin": {
        "generic_name": "Empagliflozin",
        "category": "Diabetes",
        "description": "Reduces cardiovascular mortality risk in patients with Type 2 diabetes and established cardiovascular disease.",
        "common_strengths": ["10mg", "25mg"],
        "pmbjp_price": 48.00,
        "market_avg_price": 280.00,
        "how_to_use": "Take once daily in the morning with or without food.",
        "side_effects": ["Urinary tract infection", "Dehydration", "Thirst"],
        "brands": ["Jardiance 10", "Jardiance 25", "Gibtulio 10", "Empaglyn 10"],
    },
    "Voglibose": {
        "generic_name": "Voglibose",
        "category": "Diabetes",
        "description": "Delays absorption of dietary carbohydrates to curb post-meal glucose spikes.",
        "common_strengths": ["0.2mg", "0.3mg"],
        "pmbjp_price": 12.00,
        "market_avg_price": 75.00,
        "how_to_use": "Take immediately before or with the very first bite of each main meal.",
        "side_effects": ["Flatulence", "Loose stools", "Abdominal discomfort"],
        "brands": ["Volibo 0.2", "Voglistar 0.2", "Vocarb 0.2", "Vogly 0.2", "PPG 0.2"],
    },

    # ----------------------------------------------------
    # 6. Blood Pressure, Cardiology & Statins
    # ----------------------------------------------------
    "Amlodipine": {
        "generic_name": "Amlodipine",
        "category": "Blood Pressure & Heart",
        "description": "Relaxes vascular smooth muscles; foundational antihypertensive and angina medicine.",
        "common_strengths": ["2.5mg", "5mg", "10mg"],
        "pmbjp_price": 6.50,
        "market_avg_price": 35.00,
        "how_to_use": "Take once daily at the same time each day.",
        "side_effects": ["Ankle swelling", "Flushing", "Fatigue"],
        "brands": ["Amlong 5", "Stamlo 5", "Norvasc 5", "Amlovas 5", "Amlopin 5", "Amloz 5"],
    },
    "Telmisartan": {
        "generic_name": "Telmisartan",
        "category": "Blood Pressure & Heart",
        "description": "Mainstay blood pressure therapy with 24-hour hemodynamic stability and organ protection.",
        "common_strengths": ["20mg", "40mg", "80mg"],
        "pmbjp_price": 16.00,
        "market_avg_price": 95.00,
        "how_to_use": "Take once daily with or without food. Monitor blood pressure regularly.",
        "side_effects": ["Dizziness", "Back pain", "Sinus congestion"],
        "brands": ["Telma 40", "Telmikind 40", "Tazloc 40", "Telpres 40", "Cresar 40", "Telvas 40"],
    },
    "Telmisartan + Amlodipine": {
        "generic_name": "Telmisartan + Amlodipine",
        "category": "Blood Pressure & Heart",
        "description": "Synergistic ARB + CCB combination for hypertension not controlled by monotherapy.",
        "common_strengths": ["40mg + 5mg"],
        "pmbjp_price": 24.00,
        "market_avg_price": 155.00,
        "how_to_use": "Take once daily, preferably in the morning.",
        "side_effects": ["Peripheral edema", "Dizziness", "Headache"],
        "brands": ["Telma-AM", "Sartel-AM", "Telsartan-AM", "Telmikind-AM", "Cresar-AM", "Tazloc-AM"],
    },
    "Losartan Potassium": {
        "generic_name": "Losartan Potassium",
        "category": "Blood Pressure & Heart",
        "description": "Antihypertensive agent indicated for high blood pressure and diabetic nephropathy.",
        "common_strengths": ["25mg", "50mg"],
        "pmbjp_price": 14.00,
        "market_avg_price": 68.00,
        "how_to_use": "Take with or without food. Stay adequately hydrated.",
        "side_effects": ["Dizziness", "Nasal congestion", "Back pain"],
        "brands": ["Losar 50", "Repace 50", "Tozaar 50", "Covance 50", "Alsartan 50"],
    },
    "Atenolol": {
        "generic_name": "Atenolol",
        "category": "Blood Pressure & Heart",
        "description": "Lowers heart rate and blood pressure; protects heart after myocardial infarction.",
        "common_strengths": ["25mg", "50mg"],
        "pmbjp_price": 8.00,
        "market_avg_price": 40.00,
        "how_to_use": "Take at a regular time every day. Do not stop abruptly.",
        "side_effects": ["Slow heart rate", "Cold extremities", "Fatigue"],
        "brands": ["Aten 50", "Betacard 50", "Tenolol 50", "Atpark 50"],
    },
    "Metoprolol Succinate": {
        "generic_name": "Metoprolol Succinate",
        "category": "Blood Pressure & Heart",
        "description": "Extended-release beta-blocker for hypertension, heart failure, and tachyarrhythmias.",
        "common_strengths": ["25mg", "50mg"],
        "pmbjp_price": 18.00,
        "market_avg_price": 85.00,
        "how_to_use": "Take with or immediately after a meal.",
        "side_effects": ["Fatigue", "Dizziness", "Bradycardia"],
        "brands": ["Betaloc 50", "Metolar-XR 50", "Starpress-XL 50", "Met-XL 50", "Revelol-XL 50"],
    },
    "Atorvastatin": {
        "generic_name": "Atorvastatin",
        "category": "Blood Pressure & Heart",
        "description": "Lowers LDL bad cholesterol and triglycerides; prevents heart attack and ischemic stroke.",
        "common_strengths": ["10mg", "20mg", "40mg"],
        "pmbjp_price": 18.00,
        "market_avg_price": 98.00,
        "how_to_use": "Take once daily at bedtime for optimal cholesterol synthesis inhibition.",
        "side_effects": ["Muscle ache", "Headache", "Joint pain"],
        "brands": ["Atorva 10", "Atorva 20", "Storvas 10", "Lipikind 10", "Tonact 10", "Atchol 10"],
    },
    "Rosuvastatin": {
        "generic_name": "Rosuvastatin",
        "category": "Blood Pressure & Heart",
        "description": "Potent lipid-lowering agent for hypercholesterolemia and coronary atherosclerosis.",
        "common_strengths": ["5mg", "10mg", "20mg"],
        "pmbjp_price": 26.00,
        "market_avg_price": 195.00,
        "how_to_use": "Take once daily anytime with or without food.",
        "side_effects": ["Muscle pain", "Weakness", "Nausea"],
        "brands": ["Rosuvas 10", "Rozucor 10", "Rosave 10", "Roseday 10", "Novastat 10", "Crevast 10"],
    },
    "Clopidogrel": {
        "generic_name": "Clopidogrel",
        "category": "Blood Pressure & Heart",
        "description": "Inhibits platelet aggregation to prevent arterial blood clots following stent placement or stroke.",
        "common_strengths": ["75mg"],
        "pmbjp_price": 19.00,
        "market_avg_price": 95.00,
        "how_to_use": "Take once daily. Avoid unprescribed pain killers (NSAIDs) to prevent bleeding.",
        "side_effects": ["Bleeding tendency", "Easy bruising", "Dyspepsia"],
        "brands": ["Deplatt 75", "Clopilet 75", "Plavix 75", "Ceruvit 75", "Noklot 75"],
    },
    "Aspirin (Acetylsalicylic Acid)": {
        "generic_name": "Aspirin (Acetylsalicylic Acid)",
        "category": "Blood Pressure & Heart",
        "description": "Low-dose cardioprotective agent preventing secondary thrombotic events.",
        "common_strengths": ["75mg", "150mg"],
        "pmbjp_price": 4.50,
        "market_avg_price": 15.00,
        "how_to_use": "Take with or after food. Swallow whole; do not crush enteric-coated tablets.",
        "side_effects": ["Heartburn", "Stomach irritation", "Easy bruising"],
        "brands": ["Ecosprin 75", "Ecosprin 150", "Disprin", "Delisprin 75", "Loprin 75"],
    },

    # ----------------------------------------------------
    # 7. Thyroid, Vitamins & Mineral Supplements
    # ----------------------------------------------------
    "Levothyroxine Sodium": {
        "generic_name": "Levothyroxine Sodium",
        "category": "Thyroid & Vitamins",
        "description": "Replacement therapy for hypothyroidism and congenital goiter management.",
        "common_strengths": ["25mcg", "50mcg", "75mcg", "100mcg"],
        "pmbjp_price": 22.00,
        "market_avg_price": 140.00,
        "how_to_use": "Take on an empty stomach immediately upon waking, 30-60 minutes before tea or breakfast.",
        "side_effects": ["Palpitations (if dose too high)", "Insomnia", "Weight loss"],
        "brands": ["Thyronorm 50", "Thyronorm 100", "Eltroxin 50", "Thyrox 50", "L-Thyroxine 50"],
    },
    "Calcium Carbonate + Vitamin D3": {
        "generic_name": "Calcium Carbonate + Vitamin D3",
        "category": "Thyroid & Vitamins",
        "description": "Essential bone building supplement for osteoporosis, fractures, and pregnancy nutrition.",
        "common_strengths": ["500mg + 250IU"],
        "pmbjp_price": 24.00,
        "market_avg_price": 125.00,
        "how_to_use": "Take after meals with water. Do not take at the same time as iron or thyroid medicine.",
        "side_effects": ["Constipation", "Flatulence", "Mild bloating"],
        "brands": ["Shelcal 500", "Gemcal", "Cipcal 500", "Calcimax 500", "Tayo 500", "Sandocal 500"],
    },
    "Cholecalciferol (Vitamin D3 60k)": {
        "generic_name": "Cholecalciferol (Vitamin D3 60k)",
        "category": "Thyroid & Vitamins",
        "description": "Weekly therapeutic dose for severe Vitamin D deficiency, rickets, and bone pain.",
        "common_strengths": ["60,000 IU"],
        "pmbjp_price": 35.00,
        "market_avg_price": 160.00,
        "how_to_use": "Take once a week with a milk-containing or fatty meal to maximize lipid absorption.",
        "side_effects": ["Hypercalcemia (only with chronic accidental overdose)"],
        "brands": ["Uprise-D3 60K", "Calcirol 60K", "D3 Must 60K", "Depura 60K", "Lumia 60K", "Arachitol 60K"],
    },
    "Vitamin B Complex + Vitamin B12": {
        "generic_name": "Vitamin B Complex + Vitamin B12",
        "category": "Thyroid & Vitamins",
        "description": "Supports nerve regeneration, relieves diabetic neuropathy, numbness, and mouth ulcers.",
        "common_strengths": ["Capsule / Tablet"],
        "pmbjp_price": 12.00,
        "market_avg_price": 52.00,
        "how_to_use": "Take once daily after food. May turn urine bright fluorescent yellow (harmless).",
        "side_effects": ["Bright yellow urine (normal)", "Mild nausea"],
        "brands": ["Becosules", "Neurobion Forte", "Cobadex Forte", "Optineuron", "Polybion"],
    },
    "Vitamin C (Ascorbic Acid)": {
        "generic_name": "Vitamin C (Ascorbic Acid)",
        "category": "Thyroid & Vitamins",
        "description": "Boosts immune defense, enhances collagen synthesis, and accelerates wound healing.",
        "common_strengths": ["500mg chewable"],
        "pmbjp_price": 6.50,
        "market_avg_price": 32.00,
        "how_to_use": "Chew one tablet daily. Pleasant citrus flavor.",
        "side_effects": ["None with recommended dosage"],
        "brands": ["Limcee 500", "Celin 500", "Chewcee 500", "Suckcee 500"],
    },
    "Vitamin E (Tocopherol)": {
        "generic_name": "Vitamin E (Tocopherol)",
        "category": "Thyroid & Vitamins",
        "description": "Protects cell membranes; widely used for skin repair, hair health, and muscle cramps.",
        "common_strengths": ["400mg"],
        "pmbjp_price": 15.00,
        "market_avg_price": 42.00,
        "how_to_use": "Take one capsule daily with food.",
        "side_effects": ["Mild stomach upset"],
        "brands": ["Evion 400", "Evion 600", "E-Glow 400", "Tocofer 400"],
    },
}


# ----------------------------------------------------------------------
# Dosage form detection and Precomputed Exact Salt & Brand Indexes
# ----------------------------------------------------------------------
def detect_dosage_form(name: str, default: str = "tablet") -> str:
    """
    Detects dosage form (tablet, syrup, capsule, injection, drops, etc.)
    from the medicine name or formulation string.
    """
    n = name.lower()
    if re.search(r"\b(syrup|suspension|oral liquid|elixir|liquid)\b", n) or "syrup" in n or "suspension" in n:
        return "syrup"
    if re.search(r"\b(capsule|capsules|cap|caps)\b", n):
        return "capsule"
    if re.search(r"\b(injection|inj|infusion|vial|ampoule)\b", n):
        return "injection"
    if re.search(r"\b(drop|drops|eye drop|ear drop|nasal drop|pediatric drops)\b", n):
        return "drops"
    if re.search(r"\b(gel|ointment|cream|lotion|emulgel)\b", n):
        return "ointment"
    if re.search(r"\b(inhaler|rotacap|respule|inhalation)\b", n):
        return "inhaler"
    return default


def _normalize_name(name: str) -> str:
    """Strip punctuation, casing, dosage numbers for clean token comparison."""
    cleaned = re.sub(r"[^a-zA-Z0-9\s]", " ", name).lower()
    return " ".join(cleaned.split())


# Global indexes for exact salt mapping and typo resolution
BRAND_TO_SALT: Dict[str, str] = {}
BRAND_CATALOG: Dict[str, Dict[str, Any]] = {}
SEARCHABLE_NAMES_MAP: Dict[str, Tuple[str, str, str, bool]] = {}
# Map key: cleaned_name -> (canonical_name, salt_key, dosage_form, is_brand)
SALT_TO_BRANDS_INDEX: Dict[str, List[Dict[str, Any]]] = {}

for salt_key, data in SALT_DICTIONARY.items():
    default_form = data.get("default_form", "tablet")
    generic_name = data.get("generic_name", salt_key)

    # Precise active salt list per entry
    active_salts = data.get("active_salts")
    if not active_salts:
        active_salts = [s.strip() for s in generic_name.split("+")]

    # Index salt / generic itself
    norm_salt = _normalize_name(salt_key)
    SEARCHABLE_NAMES_MAP[norm_salt] = (salt_key, salt_key, default_form, False)

    norm_generic = _normalize_name(generic_name)
    if norm_generic not in SEARCHABLE_NAMES_MAP:
        SEARCHABLE_NAMES_MAP[norm_generic] = (generic_name, salt_key, default_form, False)

    SALT_TO_BRANDS_INDEX[salt_key] = []

    for brand_item in data.get("brands", []):
        if isinstance(brand_item, dict):
            b_name = brand_item["name"]
            b_form = brand_item.get("form") or detect_dosage_form(b_name, default_form)
            b_strength = brand_item.get("strength", "")
        else:
            b_name = str(brand_item)
            b_form = detect_dosage_form(b_name, default_form)
            b_strength = ""

        brand_info = {
            "name": b_name,
            "form": b_form,
            "strength": b_strength,
            "generic_name": generic_name,
            "salt_key": salt_key,
            "active_salts": active_salts,
        }
        SALT_TO_BRANDS_INDEX[salt_key].append(brand_info)

        norm_brand = _normalize_name(b_name)
        BRAND_TO_SALT[norm_brand] = salt_key
        BRAND_CATALOG[norm_brand] = brand_info
        SEARCHABLE_NAMES_MAP[norm_brand] = (b_name, salt_key, b_form, True)

        # 1. Base brand stripping dosage/numbers: "Augmentin 625 Duo" -> "Augmentin"
        base1 = re.sub(r"\b\d+.*$", "", b_name).strip()
        if base1 and len(base1) >= 3:
            norm_b1 = _normalize_name(base1)
            if norm_b1 not in SEARCHABLE_NAMES_MAP:
                SEARCHABLE_NAMES_MAP[norm_b1] = (b_name, salt_key, b_form, True)

        # 2. First alphanumeric token: "Telma-AM" -> "Telma", "Pan-D" -> "Pan"
        first_token = b_name.split()[0].replace("-", " ")
        first_token = re.sub(r"[^a-zA-Z]", "", first_token)
        if len(first_token) >= 3:
            norm_tok = _normalize_name(first_token)
            if norm_tok not in SEARCHABLE_NAMES_MAP:
                SEARCHABLE_NAMES_MAP[norm_tok] = (b_name, salt_key, b_form, True)


ALL_SEARCHABLE_KEYS = list(SEARCHABLE_NAMES_MAP.keys())


def _build_result(
    canonical_name: str,
    salt_key: str,
    target_form: str,
    entry: Dict[str, Any],
    is_brand: bool,
    confidence: float,
) -> Dict[str, Any]:
    pmbjp_price = entry.get("pmbjp_price", 20.0)
    market_avg_price = entry.get("market_avg_price", 80.0)
    savings_pct = round(((market_avg_price - pmbjp_price) / market_avg_price) * 100, 1)

    active_salts = entry.get("active_salts")
    if not active_salts:
        active_salts = [s.strip() for s in entry["generic_name"].split("+")]

    all_brands = SALT_TO_BRANDS_INDEX.get(salt_key, [])

    # Exact salt substitutes partitioned by dosage form
    # SAME FORM: strictly only brands that share identical salt AND same form
    same_form_substitutes: List[str] = [
        b["name"]
        for b in all_brands
        if b["form"] == target_form and b["name"].lower() != canonical_name.lower()
    ]

    # OTHER FORMS: clearly separated grouping (e.g. syrups, drops)
    other_form_substitutes: Dict[str, List[str]] = {}
    for b in all_brands:
        if b["form"] != target_form:
            other_form_substitutes.setdefault(b["form"], []).append(b["name"])

    return {
        "query_matched_to": canonical_name,
        "generic_name": entry["generic_name"],
        "active_salts": active_salts,
        "dosage_form": target_form,
        "category": entry.get("category", "General"),
        "description": entry.get("description", ""),
        "how_to_use": entry.get("how_to_use", "Take as directed by consulting physician."),
        "common_strengths": entry.get("common_strengths", []),
        "side_effects": entry.get("side_effects", []),
        "pmbjp_price": pmbjp_price,
        "market_avg_price": market_avg_price,
        "pmbjp_savings_percent": savings_pct,
        "brands": same_form_substitutes,
        "all_generic_substitutes": same_form_substitutes,
        "other_form_substitutes": other_form_substitutes,
        "is_brand": is_brand,
        "match_confidence": confidence,
    }


def resolve_medicine_salt(query: str, min_score: float = 75.0) -> Optional[Dict[str, Any]]:
    """
    Two-stage resolution:
    Stage 1: Uses normalization and RapidFuzz WRatio SOLELY for typo correction
             to identify the user's intended medicine or generic.
    Stage 2: Deterministic exact active salt lookup. Substitutes are strictly
             restricted to products sharing the exact active salt composition,
             partitioned and filtered by dosage form.
    """
    if not query or len(query.strip()) < 2:
        return None

    cleaned_query = _normalize_name(query)

    # 1. Exact match in index (e.g. "dolo 650", "montecip lc", "pan d")
    if cleaned_query in SEARCHABLE_NAMES_MAP:
        canonical_name, salt_key, matched_form, is_brand = SEARCHABLE_NAMES_MAP[cleaned_query]
        entry = SALT_DICTIONARY[salt_key]
        query_form = detect_dosage_form(query, default=matched_form)
        return _build_result(canonical_name, salt_key, query_form, entry, is_brand, 100.0)

    # 2. Whole word prefix / exact token containment for queries >= 4 chars
    for key in ALL_SEARCHABLE_KEYS:
        if cleaned_query == key:
            canonical_name, salt_key, matched_form, is_brand = SEARCHABLE_NAMES_MAP[key]
            entry = SALT_DICTIONARY[salt_key]
            query_form = detect_dosage_form(query, default=matched_form)
            return _build_result(canonical_name, salt_key, query_form, entry, is_brand, 95.0)

    # 3. RapidFuzz fuzzy extract using WRatio (handles typos like "augmntin", "paracitamol", "montecyp")
    match = process.extractOne(
        cleaned_query,
        ALL_SEARCHABLE_KEYS,
        scorer=fuzz.WRatio,
    )

    if match and match[1] >= min_score:
        matched_key, score, _ = match
        canonical_name, salt_key, matched_form, is_brand = SEARCHABLE_NAMES_MAP[matched_key]
        entry = SALT_DICTIONARY[salt_key]
        query_form = detect_dosage_form(query, default=matched_form)
        return _build_result(canonical_name, salt_key, query_form, entry, is_brand, float(score))

    return None

