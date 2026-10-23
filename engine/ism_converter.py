"""
=========================================================================================
SHABANA IME - ADVANCED DVBW / ISM CONVERTER ENGINE (V6.4 - ENTERPRISE EDITION)
=========================================================================================
Architectural Highlights:
- Font Mapping Corrected: Re-aligned 'क', 'ण', and 'न' to match the correct DVBW ASCII.
- Deep Semantic Clustering: Processes complex N-depth consonants dynamically.
- Procedural Farra Injection: Dynamically applies 'Ï' and 'Òü' for R-kaar clusters.
- Terminal Modifier Sorting: Safely layers Anuswar, Visarga, and Chandrabindu AFTER Reph.
- Halant Awareness: Safely bounds non-joining characters (ट, द, ह) with visual halants.
- Dynamic Conjunct Builder: Replaces hardcoded dictionaries for infinite depth resolution.
- "Golden Injection Rule": Intersects character stems to correctly seat bottom matras.
=========================================================================================
"""

import re
import json
import os
import logging
import unicodedata
from functools import lru_cache

# =======================================================================================
# 1. SYSTEM CONFIGURATION & LOGGING
# =======================================================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
UNKNOWN_CLUSTERS_LOG = os.path.join(DATA_DIR, "unknown_clusters.txt")
DVBW_DATA_PATH = os.path.join(DATA_DIR, "dvbw_dictionary.json")

os.makedirs(DATA_DIR, exist_ok=True)

class RuntimeDiagnostics:
    """Tracks runtime anomalies and caches unknown physical ligature states."""
    _logged_clusters = set()

    @staticmethod
    def log_unknown_cluster(cluster):
        if cluster in RuntimeDiagnostics._logged_clusters:
            return
        try:
            with open(UNKNOWN_CLUSTERS_LOG, "a", encoding="utf-8") as f:
                f.write(cluster + "\n")
            RuntimeDiagnostics._logged_clusters.add(cluster)
        except Exception as e:
            logging.error(f"Failed to log unknown cluster: {e}")


# =======================================================================================
# 2. CORE MAPPING CONSTANTS (DVBW ASCII LAYOUT)
# =======================================================================================

class ISMMaps:
    """
    Contains all fundamental mapping tables for standard Unicode to DVBW translation.
    These mappings align with the standard C-DAC ISM V6 keyboard architecture.
    """
    
    # --- STANDALONE VOWELS (SWAR) ---
    VOWEL_MAP = {
        "अ": "†", "आ": "†Ö", "इ": "‡", "ई": "‡Ô", "उ": "ˆ", "ऊ": "‰",
        "ऋ": "Š", "ए": "‹", "ऐ": "‹ê", "ओ": "†Öê", "औ": "†Öî",
        "अं": "†Ó", "अः": "†„",
        "ॲ": "†ò", "ऑ": "†Öò"  
    }

    # --- BASE CONSONANTS (VYANJAN) ---
    CONSONANT_MAP = {
        "क": "Ûú", "ख": "ÜÖ", "ग": "ÝÖ", "घ": "‘Ö", "ङ": "’û",
        "च": "“Ö", "छ": "”û", "ज": "•Ö", "झ": "—Ö", "ञ": "˜Ö",
        "ट": "™ü", "ठ": "šü", "ड": "›ü", "ढ": "œü", "ण": "ÞÖ",
        "त": "ŸÖ", "थ": "£Ö", "द": "¤ü", "ध": "¬Ö", "न": "®Ö",
        "प": "¯Ö", "फ": "±ú", "ब": "²Ö", "भ": "³Ö", "म": "´Ö",
        "य": "µÖ", "र": "¸ü", "ल": "»Ö", "व": "¾Ö",
        "श": "¿Ö", "ष": "ÂÖ", "स": "ÃÖ", "ह": "Æü", "ळ": "ôû"
    }

    # --- NUKTA CONSONANTS (URDU / HINDI LOANS) ---
    NUKTA_MAP = {
        "क़": "ú", "ख़": "ÜÖ", "ग़": "ÝÖ", "ज़": "•Ö", "ड़": "›ü", "ढ़": "œü", "फ़": "±ú"
    }

    # --- DEPENDENT VOWEL SIGNS (MATRAS) ---
    MATRA_MAP = {
        "ा": "Ö", "ि": "×", "ी": "ß", "ु": "ã", "ू": "æ",
        "े": "ê", "ै": "î", "ो": "Öê", "ौ": "Öî",
        "ृ": "é", "ं": "Ó", "ः": "„", "ँ": "ò",
        "ॅ": "ò", "ॉ": "Öò", 
        "ँ": "Ñ",
        "्": "Ë"  # 🔥 ADDED: DVBW Visual Halant
    }

    # --- NUMERALS & PUNCTUATION ---
    MARATHI_NUMBER_MAP = {
        "०": "0", "१": "1", "२": "2", "३": "3", "४": "4", 
        "५": "5", "६": "6", "७": "7", "८": "8", "९": "9"
    }

    PUNCTUATION_MAP = {
        ".": ".", ",": ",", ";": ";", ":": ":",
        "?": "?", "!": "!", "-": "-", "—": "-",
        "(": "(", ")": ")", "[": "[", "]": "]",
        "{": "{", "}": "}", "/": "/", "\\": "\\",
        "'": "'", '"': '"', "‘": "'", "’": "'", 
        "“": '"', "”": '"', "|": "|"
    }

    # --- DYNAMIC VELANTI RULES ---
    VELANTI_MAP = {
        "normal": "×",       
        "wide": "×",          
        "extra_wide": "×",    
        "super_wide": "×"     
    }

    WIDE_SINGLE_CHARS = {"ख", "घ", "छ", "ध", "भ", "श", "क्ष", "ज्ञ"}
    WIDE_UNICODE_CHARS = ["ख", "घ", "छ", "ध", "भ", "श"]
    EXTRA_WIDE_CLUSTERS = ["ष्ट", "ष्ट्र", "स्ट्र", "ञ्च"]

    HALANT = "्"
    REPH_CHAR = "Ô"


# =======================================================================================
# 3. MASSIVE CONJUNCT DICTIONARY (THE LIGATURE ENGINE)
# =======================================================================================

class LigatureDictionary:
    """
    Contains only visually unique DVBW glyph definitions. 
    The rest are handled mathematically by the procedural dynamic engine.
    """
    COMPLEX_CONJUNCTS = {
        # --- Core unique ligatures ---
        "त्र": ("", "¡Ö"),
        "त्र्य": ("¡", "µÖ"),
        "क्ष": ("", "õÖ"),
        "क्ष्य": ("õ", "µÖ"),
        "क्ष्ण": ("õ", "Ö"),
        "क्ष्म": ("õ", "´Ö"),
        "ज्ञ": ("", "–Ö"),
        "ज्ञ्य": ("–", "µÖ"),
        "श्र": ("", "ÁÖ"),
        
        # --- Da/Dha special mappings ---
        "द्य": ("", "ªÖ"),
        "द्व": ("", "«Ö"),
        "द्ध": ("", "¨Ö"),
        "द्म": ("", "©Ö"),

        # --- Base extensions ---
        "क्त्र": ("", "¡Ö"),
    }

    DVBW_OVERRIDES = {
        "महाराष्ट्र": "´ÖÆüÖ¸üÖÂ™Òü",
        "भ्रष्टाचार": "³ÖÏÂ™Ö“ÖÖ¸ü",
        "राष्ट्रीय": "¸üÖÂ™ÒüßµÖ",
        "इस्त्री": "‡Ã¡Öß",
        "उद्देश": "ˆ§ê¿Ö",
        "महत्त्व": "´ÖÆüŸ¾Ö",
    }


# =======================================================================================
# 4. GOLDEN DICTIONARY MANAGER
# =======================================================================================

class GoldenDictionary:
    """Singleton class to load and hold the user's explicit correct definitions from JSON."""
    _instance = None
    _data = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoldenDictionary, cls).__new__(cls)
            cls._load_data()
        return cls._instance

    @classmethod
    def _load_data(cls):
        if os.path.exists(DVBW_DATA_PATH):
            try:
                with open(DVBW_DATA_PATH, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    if isinstance(raw_data, list):
                        cls._data = {item.get('mr', ''): item.get('dvbw', '') for item in raw_data if 'dvbw' in item}
                    elif isinstance(raw_data, dict):
                        cls._data = raw_data
                logging.info(f"Loaded {len(cls._data)} golden DVBW definitions.")
            except Exception as e:
                logging.error(f"Failed to load Golden Dictionary: {e}")

    @classmethod
    def get(cls, word):
        return cls._data.get(word)

GoldenDictionary()


# =======================================================================================
# 5. UNICODE SANITIZER
# =======================================================================================

class UnicodeSanitizer:
    """Pre-processes strings to remove invisible artifacts, ZWJs, and normalize encodings."""
    
    @staticmethod
    def clean(text):
        if not text:
            return ""
            
        text = unicodedata.normalize('NFC', text)
        text = text.replace('\u200d', '').replace('\u200c', '')
        
        for nukta, base in ISMMaps.NUKTA_MAP.items():
            text = text.replace(nukta, base)
            
        return text


# =======================================================================================
# 6. MATHEMATICAL ENGINE CORE
# =======================================================================================

class ISMEngine:
    """Calculates dynamic DVBW physical outputs for complex linguistic structures."""

    # 🔥 FIX: Registry of characters that cannot be physically split
    NON_JOINING_CONSONANTS = {"ङ", "छ", "ट", "ठ", "ड", "ढ", "द", "ह", "र", "ळ"}

    @staticmethod
    def get_half_char(consonant):
        full_code = ISMMaps.CONSONANT_MAP.get(consonant, consonant)
        # Apply visual halant fallback for non-joiners
        if consonant in ISMEngine.NON_JOINING_CONSONANTS and full_code != consonant:
            return full_code + "Ë"
        return full_code[0] if full_code else consonant

    @staticmethod
    def build_dynamic_cluster(cluster):
        letters = cluster.replace(ISMMaps.HALANT, "")
        if not letters:
            return "", ""

        if len(letters) == 1:
            return "", ISMMaps.CONSONANT_MAP.get(letters, letters)

        half_part = "".join(ISMEngine.get_half_char(l) for l in letters[:-1])
        full_part = ISMMaps.CONSONANT_MAP.get(letters[-1], letters[-1])

        return half_part, full_part

    @staticmethod
    @lru_cache(maxsize=4096)
    def process_word(text):
        result = ""
        i, n = 0, len(text)
        
        bottom_matras = {ISMMaps.MATRA_MAP["ु"], ISMMaps.MATRA_MAP["ू"], ISMMaps.MATRA_MAP["ृ"]} 
        tail_chars = {"ú", "û", "ü"}

        while i < n:
            ch = text[i]

            # 1. Bypass English characters, Numbers, and Punctuation
            if ch in ISMMaps.MARATHI_NUMBER_MAP:
                result += ISMMaps.MARATHI_NUMBER_MAP[ch]
                i += 1; continue
                
            if ch in ISMMaps.PUNCTUATION_MAP:
                result += ISMMaps.PUNCTUATION_MAP[ch]
                i += 1; continue
                
            if ch.isascii() and not ch.isalpha():
                result += ch
                i += 1; continue

            # 2. Standalone Vowels (e.g., अ, आ, ओ)
            if i + 1 < n and text[i:i+2] in ISMMaps.VOWEL_MAP:
                result += ISMMaps.VOWEL_MAP[text[i:i+2]]; i += 2; continue
            if ch in ISMMaps.VOWEL_MAP:
                result += ISMMaps.VOWEL_MAP[ch]; i += 1; continue

            # 3. Consonants and Clusters
            if ch in ISMMaps.CONSONANT_MAP or (ch == "र" and i + 1 < n and text[i+1] == ISMMaps.HALANT):
                has_reph, cluster, matras = False, "", []
                
                # Check for R-Farra (Reph) explicitly
                if ch == "र" and i + 1 < n and text[i+1] == ISMMaps.HALANT:
                    if i + 2 < n and text[i+2] in ISMMaps.CONSONANT_MAP:
                        has_reph, i = True, i + 2
                        ch = text[i]

                # Accumulate the full consonant cluster (e.g., क + ् + त = क्त)
                while i < n:
                    if text[i] in ISMMaps.CONSONANT_MAP:
                        cluster += text[i]
                        i += 1
                        if i < n and text[i] == ISMMaps.HALANT:
                            if i + 1 < n and text[i+1] in ISMMaps.CONSONANT_MAP:
                                cluster += ISMMaps.HALANT
                                i += 1
                                continue
                            else:
                                matras.append(ISMMaps.HALANT)
                                i += 1
                                break
                        else: break
                    else: break

                if not cluster:
                    result += ISMEngine.get_half_char("र") if has_reph else ch
                    i += 1
                    continue

                # Collect all trailing matras
                while i < n and text[i] in ISMMaps.MATRA_MAP:
                    matras.append(text[i])
                    i += 1

                clean_cluster = cluster.rstrip(ISMMaps.HALANT)
                
                # SPECIAL EXCEPTION: Ru (रु) and Roo (रू)
                is_ru = False
                half_part, full_part = "", ""
                
                if clean_cluster == "र":
                    if "ु" in matras:
                        full_part = "¹"
                        matras.remove("ु")
                        is_ru = True
                    elif "ू" in matras:
                        full_part = "º"
                        matras.remove("ू")
                        is_ru = True

                if not is_ru:
                    base_tuple = None
                    
                    # 🔥 PRIORITY: Longest Conjunct Match (Maximal Munch Algorithm)
                    for size in range(len(clean_cluster), 0, -1):
                        sub = clean_cluster[:size]
                        if sub in LigatureDictionary.COMPLEX_CONJUNCTS:
                            base_tuple = LigatureDictionary.COMPLEX_CONJUNCTS[sub]
                            break

                    # 🔥 FIX: Procedural Farra (R-Kaar) injection
                    if not base_tuple and len(clean_cluster) >= 3 and clean_cluster.endswith(ISMMaps.HALANT + "र"):
                        farra_base = clean_cluster[:-2]
                        
                        for size in range(len(farra_base), 0, -1):
                            sub = farra_base[:size]
                            if sub in LigatureDictionary.COMPLEX_CONJUNCTS:
                                base_tuple = LigatureDictionary.COMPLEX_CONJUNCTS[sub]
                                break
                                
                        if not base_tuple:
                            base_tuple = ISMEngine.build_dynamic_cluster(farra_base)
                            
                        h_part, f_part = base_tuple
                        
                        # Apply standard vs T-group Farra
                        if f_part == "¤ü":
                            f_part = "¦ü"  # DVBW special Dra
                        elif f_part and any(f_part.startswith(ISMMaps.CONSONANT_MAP[c][0]) for c in ["ट", "ठ", "ड", "ढ"]):
                            f_part = f_part.replace("ü", "Òü")
                        else:
                            f_part += "Ï"
                            
                        base_tuple = (h_part, f_part)

                    if not base_tuple:
                        # Log the fallback execution
                        RuntimeDiagnostics.log_unknown_cluster(clean_cluster)
                        base_tuple = ISMEngine.build_dynamic_cluster(clean_cluster)

                    half_part, full_part = base_tuple

                # Process Velanti (ि) Width Requirements
                velanti, postfix, terminal = "", "", ""
                selected_velanti = ISMMaps.VELANTI_MAP["normal"] 
                
                if "ि" in matras:
                    raw_letters = clean_cluster.replace(ISMMaps.HALANT, "")
                    num_consonants = len(raw_letters)
                    
                    if num_consonants == 1:
                        if raw_letters in ISMMaps.WIDE_SINGLE_CHARS:
                            selected_velanti = ISMMaps.VELANTI_MAP["wide"]
                        else:
                            selected_velanti = ISMMaps.VELANTI_MAP["normal"]
                    elif num_consonants == 2:
                        selected_velanti = ISMMaps.VELANTI_MAP["wide"]
                    elif num_consonants == 3:
                        selected_velanti = ISMMaps.VELANTI_MAP["extra_wide"]
                    elif num_consonants >= 4:
                        selected_velanti = ISMMaps.VELANTI_MAP["super_wide"]

                # THE GOLDEN INJECTION RULE & TERMINAL SORTING
                final_full_part = full_part

                for m in matras:
                    if m == "ि": 
                        velanti += selected_velanti
                    elif m != ISMMaps.HALANT: 
                        mapped_m = ISMMaps.MATRA_MAP[m]
                        
                        # 🔥 FIX: Split Kana (Ö) from Ardhachandra (ò) to ensure Reph seats accurately
                        if mapped_m == "Öò":
                            postfix += "Ö"
                            terminal += "ò"
                        # 🔥 FIX: Terminal Modifiers (Anuswar, Visarga) MUST sit absolutely last (AFTER the Reph)
                        elif mapped_m in {ISMMaps.MATRA_MAP.get("ं"), ISMMaps.MATRA_MAP.get("ँ"), ISMMaps.MATRA_MAP.get("ः"), ISMMaps.MATRA_MAP.get("ॅ")}:
                            terminal += mapped_m
                        # Normal Golden Injection for bottom matras
                        elif mapped_m in bottom_matras and final_full_part and final_full_part[-1] in tail_chars:
                            tail = final_full_part[-1]
                            base = final_full_part[:-1]
                            final_full_part = base + mapped_m + tail
                        else:
                            postfix += mapped_m
                    elif m == ISMMaps.HALANT:
                        postfix += ISMMaps.MATRA_MAP[m]

                # Construct the physical keystroke sequence
                # Order: [Velanti] + [Half Consonants] + [Full Base] + [Postfix Matras] + [Reph] + [Terminal Modifiers]
                result += velanti + half_part + final_full_part + postfix + (ISMMaps.REPH_CHAR if has_reph else "") + terminal
                continue

            # 4. Standalone Matras (Fallback)
            if ch in ISMMaps.MATRA_MAP:
                result += ISMMaps.MATRA_MAP[ch]; i += 1; continue
                
            result += ch; i += 1
            
        return result


# =======================================================================================
# 7. PUBLIC API (WRAPPER FUNCTION)
# =======================================================================================

def unicode_to_ism(text):
    """
    Public entry point for the ISM Engine.
    Translates a Marathi Unicode string into DVBW ASCII.
    """
    clean_text = UnicodeSanitizer.clean(text)
    
    if not clean_text:
        return ""
        
    tokens = re.split(r'(\s+)', clean_text)
    out = []

    for t in tokens:
        clean = t.strip()

        if not clean:
            out.append(t)
            continue

        golden_val = GoldenDictionary.get(clean)
        if golden_val:
            out.append(golden_val)
        elif clean in LigatureDictionary.DVBW_OVERRIDES:
            out.append(LigatureDictionary.DVBW_OVERRIDES[clean])
        else:
            out.append(ISMEngine.process_word(clean))

    return "".join(out)