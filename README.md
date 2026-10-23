# Shabana Smart Pratigyapatra (शबाना स्मार्ट प्रतिज्ञापत्र)
### *Affidavit Master & Intelligent Template Studio for CSC Centers*

**Shabana Smart Pratigyapatra** is a specialized desktop application built for CSC (Common Service Center) operators and MahaOnline service providers across Maharashtra. It enables rapid drafting, automated template mining from legacy Word documents, and real-time live preview of affidavits and legal declarations in Marathi (Mangal Unicode) and ISM (DVBW Shree-Lipi).

---

## 🌟 Key Features

1. **Dual-Pane Live Preview**
   - **Left Pane:** Categorized form fields (Applicant details, heirs, Gazette changes, etc.) with intuitive inputs.
   - **Right Pane:** Real-time A4 document preview that reflects your edits instantaneously without re-generating files.

2. **Bulk Bold-Letter Template Extractor**
   - Ingests entire folders containing hundreds of pre-filled legacy `.docx` files.
   - Automatically detects data filled in **bold letters** (Mangal font) and converts them into smart template variables (e.g., `{applicant_name}`, `{aadhaar_no}`).
   - **Smart Deduplication:** Identifies repeated multi-page person entries (e.g., Ramesh on Page 1, Dharmesh on Page 2) and removes duplicate template instances.

3. **Maharashtra Affidavit Suite**
   - वारस प्रतिज्ञापत्र (Heirship Affidavit) with dynamic heir table generation.
   - विवाहानंतर नाव बदलाबाबत प्रतिज्ञापत्र (Gazette Name Change Declaration).
   - उत्पन्न / वय / रहिवासी प्रतिज्ञापत्र (Income, Age & Domicile Affidavits).
   - ऑटो बारकोड जनरेशन (Barcode integration for document verification).

4. **Dual Font & Script Engine**
   - Native Marathi Unicode (Mangal font).
   - Built-in ISM / DVBW Shree-Lipi bi-directional conversion engine.

---

## 📁 Project Structure

```
templete_generator/
│
├── engine/
│   └── ism_converter.py        # ISM (DVBW Shree-Lipi) Unicode converter
├── data/
│   └── unknown_clusters.txt    # Mapping reference for character conversions
├── docx_export.py              # Word document generation with styles & tables
├── main.py                     # GUI Application (CustomTkinter)
├── template_parser.py          # Placeholder extraction and document filler
├── templates.py                # Built-in affidavit definitions & fields
├── requirements.txt            # Python dependencies
└── README.md                   # Documentation
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Microsoft Word (recommended for viewing exported `.docx`)
- Mangal font (standard Windows Hindi/Marathi font)

### Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/jameerh/Shabana-Smart-Pratigyapatra.git
   cd Shabana-Smart-Pratigyapatra
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the application:
   ```bash
   python main.py
   ```

---

## 🛠️ Tech Stack
- **UI Framework:** CustomTkinter / Tkinter
- **Document Processing:** `python-docx`
- **Barcode & Imaging:** `python-barcode`, `pillow`
- **Typing Engine:** Marathi Mangal (Unicode) + ISM Engine

---

## 👤 Author & Credits
- **Developer:** [jameerh](https://github.com/jameerh)
- **Part of the Shabana Suite:** Shabana Smart Sort | Shabana CSC Studio | Shabana Smart Pratigyapatra
