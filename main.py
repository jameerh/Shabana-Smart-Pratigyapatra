# main.py
import tkinter as tk
import json
import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from templates import TEMPLATES
from docx_export import export_to_docx, export_waras_template, export_waras_filled
from template_parser import extract_placeholders, create_filled_document

# Set appearance and theme
ctk.set_appearance_mode("light")   # or "dark"
ctk.set_default_color_theme("blue")

class AffidavitGenerator:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Affidavit Generator - Maharashtra")
        self.root.geometry("1300x800")
        self.root.minsize(1000, 600)

        # Mode and state variables
        self.mode = tk.StringVar(value="builtin")
        self.current_template = tk.StringVar(value="Waras (Heirship) Affidavit")
        self.use_ism = tk.BooleanVar(value=False)

        self.custom_template_path = None
        self.custom_placeholders = []
        self.custom_fields = {}          # field name -> ctk.CTkEntry
        self.builtin_fields = {}         # field name -> widget (CTkEntry or StringVar)
        self.heir_entries = []           # list of (name_entry, age_entry, rel_entry)

        # Build the main layout
        self.create_layout()
        self.load_saved_data()
        self.fill_sample()
        self.root.mainloop()

    def create_layout(self):
        # Main container with padding
        self.main_container = ctk.CTkFrame(self.root, corner_radius=15)
        self.main_container.pack(fill="both", expand=True, padx=15, pady=15)

        # Sidebar (left panel)
        self.sidebar = ctk.CTkFrame(self.main_container, width=250, corner_radius=15)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10), pady=10)

        ctk.CTkLabel(self.sidebar, text="Affidavit Tool",
                     font=("Segoe UI", 20, "bold")).pack(pady=20)

        # Mode selection
        ctk.CTkRadioButton(self.sidebar, text="Built-in Templates",
                           variable=self.mode, value="builtin",
                           command=self.on_mode_change).pack(anchor="w", padx=20, pady=5)
        ctk.CTkRadioButton(self.sidebar, text="Custom Template",
                           variable=self.mode, value="custom",
                           command=self.on_mode_change).pack(anchor="w", padx=20, pady=5)

        # Built-in template dropdown (shown only in built-in mode)
        self.builtin_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.builtin_frame.pack(fill="x", padx=20, pady=10)
        ctk.CTkLabel(self.builtin_frame, text="Affidavit Type:", anchor="w").pack(fill="x")
        self.template_combo = ctk.CTkComboBox(self.builtin_frame,
                                              values=list(TEMPLATES.keys()),
                                              variable=self.current_template,
                                              command=self.on_template_change)
        self.template_combo.pack(fill="x", pady=5)

        # Custom template button
        self.custom_btn = ctk.CTkButton(self.sidebar, text="Load Custom Template",
                                        command=self.load_custom_template)
        self.custom_btn.pack(pady=20, padx=20, fill="x")

        # Action buttons
        ctk.CTkButton(self.sidebar, text="Fill Sample Data",
                      command=self.fill_sample, fg_color="#e0e0e0", text_color="black").pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Generate Word",
                      command=self.generate_word, fg_color="#4CAF50").pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Save Data",
                      command=self.save_data, fg_color="#2196F3").pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Load Data",
                      command=self.load_data, fg_color="#FF9800").pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Generate Template (Blank)",
                      command=self.generate_template).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Export Raw Template",
                      command=self.generate_raw_template).pack(pady=5, padx=20, fill="x")
        ctk.CTkButton(self.sidebar, text="Export All Templates",
                      command=self.export_all_templates).pack(pady=5, padx=20, fill="x")

        # ISM checkbox
        self.ism_check = ctk.CTkCheckBox(self.sidebar, text="Use ISM (DVBW) Conversion",
                                         variable=self.use_ism)
        self.ism_check.pack(pady=20, padx=20, anchor="w")

        # Main content area
        self.content = ctk.CTkFrame(self.main_container, corner_radius=15)
        self.content.pack(side="left", fill="both", expand=True, pady=10)

        # Header
        header = ctk.CTkFrame(self.content, height=60, corner_radius=10)
        header.pack(fill="x", padx=10, pady=(10, 5))
        ctk.CTkLabel(header, text="Affidavit Generator",
                     font=("Segoe UI", 22, "bold")).pack(side="left", padx=15)

        # Scrollable form area (dynamic fields)
        self.form_frame = ctk.CTkScrollableFrame(self.content, corner_radius=10)
        self.form_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Preview area
        preview_frame = ctk.CTkFrame(self.content, corner_radius=10)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)
        ctk.CTkLabel(preview_frame, text="Preview", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=5)
        self.preview_text = ctk.CTkTextbox(preview_frame, font=("Mangal", 14), wrap="word")
        self.preview_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Initial UI state
        self.on_mode_change()

    def on_mode_change(self):
        """Switch between built-in and custom mode."""
        if self.mode.get() == "builtin":
            self.builtin_frame.pack(fill="x", padx=20, pady=10)
            self.custom_btn.pack_forget()
            self.on_template_change()
        else:
            self.builtin_frame.pack_forget()
            self.custom_btn.pack(pady=20, padx=20, fill="x")
            if self.custom_template_path:
                self.build_custom_form()
            else:
                self.clear_form()

    def clear_form(self):
        """Clear the dynamic form area."""
        for widget in self.form_frame.winfo_children():
            widget.destroy()
        self.preview_text.delete("0.0", "end")

    def load_custom_template(self):
        """Open file dialog, load a .docx, extract placeholders, and build form."""
        file_path = filedialog.askopenfilename(filetypes=[("Word files", "*.docx")])
        if not file_path:
            return
        try:
            self.custom_template_path = file_path
            self.custom_placeholders = extract_placeholders(file_path)
            self.build_custom_form()
            messagebox.showinfo("Success", f"Loaded template with {len(self.custom_placeholders)} placeholders.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to parse template: {e}")

    def build_custom_form(self):
        """Build entry fields for each placeholder found in the custom template."""
        self.clear_form()
        self.custom_fields.clear()

        for i, ph in enumerate(sorted(self.custom_placeholders)):
            # Card‑like container
            card = ctk.CTkFrame(self.form_frame, corner_radius=12)
            card.pack(fill="x", padx=10, pady=8)

            ctk.CTkLabel(card, text=ph.replace("_", " ").title(),
                         font=("Segoe UI", 14)).pack(anchor="w", padx=10, pady=(8, 0))
            entry = ctk.CTkEntry(card, height=35)
            entry.pack(fill="x", padx=10, pady=8)
            self.custom_fields[ph] = entry

        self.preview_text.delete("0.0", "end")
        self.preview_text.insert("0.0", f"Custom template loaded: {os.path.basename(self.custom_template_path)}\n\nPlaceholders: {', '.join(self.custom_placeholders)}")

    def on_template_change(self, event=None):
        """Built-in template selected – build built-in form."""
        if self.mode.get() != "builtin":
            return
        self.clear_form()
        self.builtin_fields = {}
        self.heir_entries = []

        template_name = self.current_template.get()
        template_info = TEMPLATES[template_name]
        fields = template_info["fields"]
        heirs_supported = template_info.get("heirs", False)

        for field in fields:
            card = ctk.CTkFrame(self.form_frame, corner_radius=12)
            card.pack(fill="x", padx=10, pady=8)

            if field == "gender":
                ctk.CTkLabel(card, text="Gender:", font=("Segoe UI", 14)).pack(anchor="w", padx=10, pady=(8, 0))
                gender_var = tk.StringVar(value="पुरुष")
                radio_frame = ctk.CTkFrame(card, fg_color="transparent")
                radio_frame.pack(anchor="w", padx=10, pady=8)
                ctk.CTkRadioButton(radio_frame, text="पुरुष", variable=gender_var, value="पुरुष").pack(side="left", padx=5)
                ctk.CTkRadioButton(radio_frame, text="स्त्री", variable=gender_var, value="स्त्री").pack(side="left", padx=5)
                self.builtin_fields[field] = gender_var
            else:
                label_text = field.replace("_", " ").title()
                ctk.CTkLabel(card, text=label_text + ":", font=("Segoe UI", 14)).pack(anchor="w", padx=10, pady=(8, 0))
                entry = ctk.CTkEntry(card, height=35)
                entry.pack(fill="x", padx=10, pady=8)
                self.builtin_fields[field] = entry

        if heirs_supported:
            # Heirs section
            heir_header = ctk.CTkFrame(self.form_frame, corner_radius=12)
            heir_header.pack(fill="x", padx=10, pady=8)
            ctk.CTkLabel(heir_header, text="Heirs (up to 5):", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=10, pady=8)

            for i in range(5):
                card = ctk.CTkFrame(self.form_frame, corner_radius=12)
                card.pack(fill="x", padx=10, pady=5)
                # Row with three entries
                row_frame = ctk.CTkFrame(card, fg_color="transparent")
                row_frame.pack(fill="x", padx=10, pady=5)
                ctk.CTkLabel(row_frame, text=f"Heir {i+1}:", width=60).pack(side="left", padx=5)
                name_e = ctk.CTkEntry(row_frame, placeholder_text="Name", width=180)
                name_e.pack(side="left", padx=5)
                age_e = ctk.CTkEntry(row_frame, placeholder_text="Age", width=80)
                age_e.pack(side="left", padx=5)
                rel_e = ctk.CTkEntry(row_frame, placeholder_text="Relation", width=120)
                rel_e.pack(side="left", padx=5)
                self.heir_entries.append((name_e, age_e, rel_e))

        # Bind update events
        for widget in self.builtin_fields.values():
            if isinstance(widget, ctk.CTkEntry):
                widget.bind("<KeyRelease>", self.update_preview)
            elif isinstance(widget, tk.StringVar):
                widget.trace("w", lambda *args: self.update_preview())
        for name_e, age_e, rel_e in self.heir_entries:
            name_e.bind("<KeyRelease>", self.update_preview)
            age_e.bind("<KeyRelease>", self.update_preview)
            rel_e.bind("<KeyRelease>", self.update_preview)

        self.update_preview()

    def get_data(self):
        """Return dict of current field values based on mode."""
        if self.mode.get() == "custom":
            data = {}
            for ph, entry in self.custom_fields.items():
                data[ph] = entry.get()
            return data

        # Built-in mode
        data = {}
        for field, widget in self.builtin_fields.items():
            if isinstance(widget, ctk.CTkEntry):
                data[field] = widget.get().strip()
            elif isinstance(widget, tk.StringVar):
                data[field] = widget.get()

        template_name = self.current_template.get()
        if TEMPLATES[template_name].get("heirs", False):
            heirs = []
            for name_e, age_e, rel_e in self.heir_entries:
                name = name_e.get().strip()
                age = age_e.get().strip()
                rel = rel_e.get().strip()
                if name or age or rel:
                    heirs.append((name, age, rel))
            data["heirs_list"] = heirs
            heir_lines = []
            for idx, (name, age, rel) in enumerate(heirs, 1):
                heir_lines.append(f"{idx}) {name} - वय {age} - {rel}")
            data["heir_table"] = "\n".join(heir_lines) if heir_lines else "कोणीही वारस नाही"
            data["number_of_heirs"] = str(len(heirs))

        if template_name == "Income Certificate (3 Years)":
            def to_int(val):
                try:
                    return int(''.join(filter(str.isdigit, val)))
                except:
                    return 0

            total1 = (to_int(data.get("income1_salary", "0")) +
                      to_int(data.get("income1_agri", "0")) +
                      to_int(data.get("income1_labour", "0")) +
                      to_int(data.get("income1_other", "0")))
            total2 = (to_int(data.get("income2_salary", "0")) +
                      to_int(data.get("income2_agri", "0")) +
                      to_int(data.get("income2_labour", "0")) +
                      to_int(data.get("income2_other", "0")))
            total3 = (to_int(data.get("income3_salary", "0")) +
                      to_int(data.get("income3_agri", "0")) +
                      to_int(data.get("income3_labour", "0")) +
                      to_int(data.get("income3_other", "0")))

            data["total1"] = f"{total1}/-"
            data["total2"] = f"{total2}/-"
            data["total3"] = f"{total3}/-"

        return data

    def update_preview(self, event=None):
        """Update preview area with current data."""
        template_name = self.current_template.get()
        data = self.get_data()

        if self.mode.get() == "custom":
            self.preview_text.delete("0.0", "end")
            self.preview_text.insert("0.0", f"Custom template loaded: {os.path.basename(self.custom_template_path)}\n\nPlaceholders: {', '.join(self.custom_placeholders)}")
            return

        # Built-in preview
        template_info = TEMPLATES[template_name]
        if "gender" in data:
            data["gender_verb"] = "सांगतो" if data["gender"] == "पुरुष" else "सांगते"
            data["gender_prefix"] = "श्री" if data["gender"] == "पुरुष" else "सौ."
        try:
            preview = template_info["template"].format(**data)
            self.preview_text.delete("0.0", "end")
            self.preview_text.insert("0.0", preview)
        except KeyError as e:
            self.preview_text.delete("0.0", "end")
            self.preview_text.insert("0.0", f"Error: Missing field {e}\n\nPlease fill all fields.")
        except Exception as e:
            self.preview_text.delete("0.0", "end")
            self.preview_text.insert("0.0", f"Error: {e}")

    def fill_sample(self):
        """Fill sample data for the current template (built-in only)."""
        if self.mode.get() == "custom":
            messagebox.showinfo("Info", "Sample data not available for custom templates.")
            return

        template_name = self.current_template.get()
        sample = {}

        if template_name == "Waras (Heirship) Affidavit":
            sample = {
                "applicant_full_name": "राम शंकर जोशी",
                "applicant_age": "45",
                "applicant_occupation": "शिक्षक",
                "applicant_taluka": "पुणे",
                "applicant_district": "पुणे",
                "deceased_relation": "वडील",
                "deceased_name": "शंकर राम जोशी",
                "deceased_death_date": "१५/०८/२०२३",
                "deceased_death_place": "पुणे",
                "city_survey_number": "गट क्र. १२३, ह. नं. ४५",
                "affidavit_place": "पुणे",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }
            # Clear and fill heirs
            for name_e, age_e, rel_e in self.heir_entries:
                name_e.delete(0, "end")
                age_e.delete(0, "end")
                rel_e.delete(0, "end")
            heirs_sample = [
                ("राम शंकर जोशी", "45", "पुत्र"),
                ("सीता शंकर जोशी", "40", "पत्नी"),
                ("मोहन शंकर जोशी", "20", "पुत्र")
            ]
            for i, (name, age, rel) in enumerate(heirs_sample):
                if i < len(self.heir_entries):
                    name_e, age_e, rel_e = self.heir_entries[i]
                    name_e.delete(0, "end")
                    name_e.insert(0, name)
                    age_e.delete(0, "end")
                    age_e.insert(0, age)
                    rel_e.delete(0, "end")
                    rel_e.insert(0, rel)

        elif template_name == "Name Change Affidavit":
            sample = {
                "applicant_full_name": "सुनिल कुमार शर्मा",
                "applicant_age": "30",
                "applicant_occupation": "व्यवसाय",
                "applicant_address": "पुणे, महाराष्ट्र",
                "old_name": "सुनिल कुमार शर्मा",
                "new_name": "सुनिल कुमार",
                "reason": "धार्मिक कारणास्तव",
                "affidavit_place": "पुणे",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }

        elif template_name == "Lost Document Affidavit":
            sample = {
                "applicant_full_name": "प्रिया जोशी",
                "applicant_age": "28",
                "applicant_occupation": "विद्यार्थी",
                "applicant_address": "मुंबई",
                "document_type": "मार्कशीट",
                "document_details": "SSC मार्कशीट, गुंडा क्र. 123",
                "lost_date": "१०/०२/२०२५",
                "lost_place": "मुंबई सेंट्रल",
                "complaint_filed": "होय, नोंद क्र. 456/25",
                "affidavit_place": "मुंबई",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "स्त्री"
            }

        elif template_name == "Date of Birth Affidavit":
            sample = {
                "applicant_full_name": "अनिल देशपांडे",
                "applicant_age": "35",
                "applicant_occupation": "अभियंता",
                "applicant_address": "नागपूर",
                "dob": "१५/०५/१९९०",
                "dob_place": "नागपूर",
                "reason": "शाळेत नोंद नसल्याने",
                "affidavit_place": "नागपूर",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }

        elif template_name == "Income Affidavit":
            sample = {
                "applicant_full_name": "सविता पाटील",
                "applicant_age": "40",
                "applicant_occupation": "शिक्षिका",
                "taluka_name": "कोल्हापूर",
                "district": "कोल्हापूर",
                "village": "शिंगणापूर",
                "financial_year": "२०२४-२०२५",
                "income_amount": "3,00,000",
                "income_in_words": "तीन लाख रुपये",
                "reason_for_document": "शासकीय योजनेचा लाभ घेण्यासाठी",
                "validity_of_document": "०१/०४/२०२६",
                "date_of_application": "१५/०३/२०२५",
                "talathi_report_date": "२०/०३/२०२५",
                "affidavit_place": "कोल्हापूर",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "स्त्री"
            }

        elif template_name == "Address Proof Affidavit":
            sample = {
                "applicant_full_name": "मनोज कुमार",
                "applicant_age": "32",
                "applicant_occupation": "व्यवसाय",
                "old_address": "औरंगाबाद",
                "new_address": "पुणे, महाराष्ट्र",
                "duration_at_new": "२ वर्षे",
                "reason": "नोकरी बदल",
                "affidavit_place": "पुणे",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }

        elif template_name == "Landless Agricultural Labour Certificate":
            sample = {
                "applicant_full_name": "सुभाष गोविंद पवार",
                "applicant_age": "42",
                "applicant_occupation": "शेतमजूर",
                "village": "वडगाव",
                "taluka_name": "पुणे",
                "district": "पुणे",
                "pincode": "411041",
                "application_reference_number": "APP/2025/001234",
                "application_date": "१०/०३/२०२५",
                "affidavit_date": "०१/०४/२०२५",
                "talathi_report_date": "१५/०३/२०२५",
                "aadhar_number": "1234 5678 9012",
                "affidavit_place": "पुणे",
                "gender": "पुरुष"
            }

        elif template_name == "Gap Certificate":
            sample = {
                "applicant_full_name": "सतिश तुकाराम शास्त्री",
                "applicant_age": "26",
                "applicant_occupation": "शिक्षण",
                "applicant_address": "मिरवाड, जत, जिल्हा सांगली",
                "institution_name": "पद्मभुषण डॉ वसंतरावदादा पाटील महाविद्यालय तासगांव",
                "qualification": "M.Sc.",
                "year_of_completion": "2023",
                "gap_start_year": "2023",
                "gap_end_year": "2025",
                "reason": "",
                "affidavit_place": "सांगली",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }

        elif template_name == "Income Certificate (3 Years)":
            sample = {
                "applicant_full_name": "विकास कुंडलिक गुरवे",
                "applicant_age": "21",
                "applicant_occupation": "शिक्षण",
                "applicant_address": "सांगली, जिल्हा सांगली",
                "year1": "2018-19",
                "year2": "2019-20",
                "year3": "2020-21",
                "income1_salary": "0/-",
                "income1_agri": "50000/-",
                "income1_labour": "0/-",
                "income1_other": "0/-",
                "income2_salary": "0/-",
                "income2_agri": "55000/-",
                "income2_labour": "0/-",
                "income2_other": "0/-",
                "income3_salary": "0/-",
                "income3_agri": "60000/-",
                "income3_labour": "0/-",
                "income3_other": "0/-",
                "affidavit_place": "सांगली",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }

        elif template_name == "Hiba (Gift) Deed":
            sample = {
                "donor_name": "अमीर महिबूब मुल्ला",
                "donor_age": "38",
                "donor_occupation": "शेती",
                "donor_address": "जत, ता. जत, जिल्हा सांगली",
                "donee_name": "आमीना कमाल शेख",
                "donee_age": "41",
                "donee_occupation": "गृहिणी",
                "donee_address": "धावडवाडी, ता. जत, जिल्हा सांगली",
                "property_description": "गट क्र. 502/1/ब/2, क्षेत्र 0.01.00 हेक्टर",
                "survey_number": "502/1/ब/2",
                "area": "0.01.00 हेक्टर",
                "boundaries": "पूर्वेस शिवाजी बापूजी जाधव यांची खुली जागा, पश्चिमेस दुधाळवस्ती ते जत हायस्कूल रस्ता, दक्षिणेस शिवाजी बापूजी जाधव यांची खुली जागा, उत्तरेस सौ. शोभा दाजी पांढरे यांची इमारत",
                "date_of_gift": "२५/१२/२०२०",
                "witness1_name": "रफिक अहमद शेख",
                "witness1_address": "बेवनूर, ता. जत, जिल्हा सांगली",
                "witness2_name": "अहमदरफिक हनीफ शेख",
                "witness2_address": "धावडवाडी, ता. जत, जिल्हा सांगली",
                "affidavit_place": "जत",
                "affidavit_date": "२८/०९/२०२१",
                "gender": "पुरुष"
            }

        elif template_name == "Alpa Bhumidhar Shetkari (Small Farmer) Affidavit":
            sample = {
                "applicant_name": "बाबूराव गणपत पवार",
                "age": "45",
                "occupation": "शेती",
                "village_name": "सोनगिरी",
                "taluka_name": "जत",
                "district_name": "सांगली",
                "gut_number": "123",
                "khata_number": "456",
                "land_area": "0.02.00 हेक्टर",
                "affidavit_place": "जत",
                "affidavit_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }
        
        elif template_name == "Marriage Affidavit":
            sample = {
                "applicant_name": "रमेश गोविंद पवार",
                "age": "28",
                "occupation": "शेती",
                "village_name": "सोनगिरी",
                "district_name": "सांगली",
                "marriage_date": "१२/०२/२०२०",
                "marriage_place": "जत",
                "spouse_father_name": "शंकरराव पाटील",
                "spouse_name_before_marriage": "सुमन शंकर पाटील",
                "spouse_name_after_marriage": "सुमन रमेश पवार",
                "affidavit_date": "०१/०४/२०२५",
                "magistrate_name": "अनिल कुमार",
                "magistrate_place": "जत",
                "magistrate_date": "०१/०४/२०२५",
                "gender": "पुरुष"
            }

        # Fill the fields
        for field, widget in self.builtin_fields.items():
            if field in sample:
                if isinstance(widget, ctk.CTkEntry):
                    widget.delete(0, "end")
                    widget.insert(0, sample[field])
                elif isinstance(widget, tk.StringVar):  # gender radio
                    widget.set(sample[field])

        self.update_preview()

    def generate_word(self):
        """Generate Word document from current mode."""
        if self.mode.get() == "custom":
            if not self.custom_template_path:
                messagebox.showerror("Error", "No custom template loaded.")
                return
            data = self.get_data()
            missing = [ph for ph in self.custom_placeholders if not data.get(ph)]
            if missing:
                messagebox.showwarning("Missing fields", f"Please fill: {', '.join(missing)}")
                return
            output_path = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word files", "*.docx")])
            if output_path:
                try:
                    create_filled_document(self.custom_template_path, data, output_path)
                    messagebox.showinfo("Success", f"Document saved as {output_path}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to generate document: {e}")
            return

        # Built-in mode
        preview_text = self.preview_text.get("0.0", "end").strip()
        if not preview_text or preview_text.startswith("Error"):
            messagebox.showerror("Error", "Please fill all fields correctly before generating Word.")
            return

        filename = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word files", "*.docx")])
        if not filename:
            return

        template_name = self.current_template.get()
        template_info = TEMPLATES[template_name]

        data = self.get_data()
        taluka_name = data.get("applicant_taluka", data.get("taluka_name", ""))
        barcode_data = None
        if "barcode_field" in template_info:
            barcode_field = template_info["barcode_field"]
            if barcode_field in data:
                barcode_data = data[barcode_field]
        if template_name == "Waras (Heirship) Affidavit":
            export_waras_filled(filename, data, taluka_name, use_ism=self.use_ism.get())
        else:
            export_to_docx(preview_text, filename, barcode_data, taluka_name, use_ism=self.use_ism.get())

        messagebox.showinfo("Success", f"Affidavit saved as {filename}")

    def generate_template(self):
        """Generate blank template (handwritten) for built-in only."""
        if self.mode.get() == "custom":
            messagebox.showinfo("Info", "Blank template generation is only available for built-in templates.")
            return

        template_name = self.current_template.get()
        filename = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word files", "*.docx")])
        if not filename:
            return

        if template_name == "Waras (Heirship) Affidavit":
            export_waras_template(filename)
            messagebox.showinfo("Success", f"Professional template saved as {filename}")
            return

        template_info = TEMPLATES[template_name]
        raw_template = template_info["template"]
        note = "\n\n[Note: This is a template file. Fill in the placeholders {...} accordingly.]"
        raw_template += note
        export_to_docx(raw_template, filename, barcode_data=None, taluka_name="", use_ism=self.use_ism.get())
        messagebox.showinfo("Success", f"Template saved as {filename}")

    def generate_raw_template(self):
        """Export raw placeholder template (code) for built-in only."""
        if self.mode.get() == "custom":
            messagebox.showinfo("Info", "Raw template export is only available for built-in templates.")
            return

        template_name = self.current_template.get()
        template_info = TEMPLATES[template_name]
        raw_template = template_info["template"]
        note = "\n\n[Note: This is a programmatic template. Placeholders like {field} will be replaced by the application.]"
        raw_template += note
        filename = filedialog.asksaveasfilename(defaultextension=".docx", filetypes=[("Word files", "*.docx")])
        if not filename:
            return
        export_to_docx(raw_template, filename, barcode_data=None, taluka_name="", use_ism=self.use_ism.get())
        messagebox.showinfo("Success", f"Raw template saved as {filename}")

    def export_all_templates(self):
        """Export all built-in templates (code) to a folder."""
        if self.mode.get() == "custom":
            messagebox.showinfo("Info", "Bulk export is only available for built-in templates.")
            return

        folder = filedialog.askdirectory(title="Select folder to save templates")
        if not folder:
            return
        count = 0
        for template_name, template_info in TEMPLATES.items():
            raw_template = template_info["template"]
            note = "\n\n[Note: This is a programmatic template. Placeholders like {field} will be replaced by the application.]"
            full_text = raw_template + note
            safe_name = template_name.replace(" ", "_").replace("(", "").replace(")", "")
            filename = os.path.join(folder, f"{safe_name}_template.docx")
            export_to_docx(full_text, filename, barcode_data=None, taluka_name="", use_ism=self.use_ism.get())
            count += 1
        messagebox.showinfo("Success", f"{count} templates exported to:\n{folder}")

    def save_data(self):
        """Save current form data to JSON."""
        data = {}
        if self.mode.get() == "custom":
            for ph, entry in self.custom_fields.items():
                data[ph] = entry.get()
        else:
            for field, widget in self.builtin_fields.items():
                if isinstance(widget, ctk.CTkEntry):
                    data[field] = widget.get()
                elif isinstance(widget, tk.StringVar):
                    data[field] = widget.get()
            template_name = self.current_template.get()
            if TEMPLATES[template_name].get("heirs", False):
                heirs = []
                for name_e, age_e, rel_e in self.heir_entries:
                    heirs.append({
                        "name": name_e.get(),
                        "age": age_e.get(),
                        "relation": rel_e.get()
                    })
                data["heirs"] = heirs

        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Success", f"Data saved to {filename}")

    def load_data(self):
        """Load saved data from JSON and populate form."""
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            if self.mode.get() == "custom":
                for ph, entry in self.custom_fields.items():
                    if ph in data:
                        entry.delete(0, "end")
                        entry.insert(0, data[ph])
            else:
                for field, widget in self.builtin_fields.items():
                    if field in data:
                        if isinstance(widget, ctk.CTkEntry):
                            widget.delete(0, "end")
                            widget.insert(0, data[field])
                        elif isinstance(widget, tk.StringVar):
                            widget.set(data[field])
                template_name = self.current_template.get()
                if TEMPLATES[template_name].get("heirs", False) and "heirs" in data:
                    for i, heir in enumerate(data["heirs"]):
                        if i < len(self.heir_entries):
                            name_e, age_e, rel_e = self.heir_entries[i]
                            name_e.delete(0, "end"); name_e.insert(0, heir.get("name", ""))
                            age_e.delete(0, "end"); age_e.insert(0, heir.get("age", ""))
                            rel_e.delete(0, "end"); rel_e.insert(0, heir.get("relation", ""))
            self.update_preview()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load data: {e}")

    def load_saved_data(self):
        if os.path.exists("data/saved.json"):
            try:
                with open("data/saved.json", "r", encoding="utf-8") as f:
                    data = json.load(f)
                if self.mode.get() == "custom":
                    for ph, entry in self.custom_fields.items():
                        if ph in data:
                            entry.delete(0, "end")
                            entry.insert(0, data[ph])
                else:
                    for field, widget in self.builtin_fields.items():
                        if field in data:
                            if isinstance(widget, ctk.CTkEntry):
                                widget.delete(0, "end")
                                widget.insert(0, data[field])
                            elif isinstance(widget, tk.StringVar):
                                widget.set(data[field])
                self.update_preview()
            except:
                pass

if __name__ == "__main__":
    app = AffidavitGenerator()