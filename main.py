# main.py
"""Shabana Smart Pratigyapatra (शबाना स्मार्ट प्रतिज्ञापत्र) - Affidavit Master
Complete Dual-Pane Live Preview Studio & Bulk Bold Template Generator
"""
import json
import os
import re
import sys
import tempfile
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from templates import TEMPLATES
from docx_export import export_to_docx, export_legacy_text_docx
from template_parser import extract_placeholders, create_filled_document
from engine.smart_docx_import import extract_docx_fields, infer_label, build_docx_preview, detect_docx_font_family
from engine.bold_template_miner import mine_docx
from engine.template_deduplicator import fingerprint_docx, classify_duplicate
from engine.section_repeater import detect_repeated_person_sections
from engine.batch_pipeline import process_template_folder

# Set CustomTkinter theme
ctk.set_appearance_mode("dark")  # Sleek modern dark mode
ctk.set_default_color_theme("blue")


class AffidavitStudio:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Shabana Smart Pratigyapatra (Affidavit Master) - Maharashtra")
        self.root.geometry("1400x880")
        self.root.minsize(1100, 700)

        # State Variables
        self.mode = tk.StringVar(value="builtin")
        self.current_template = tk.StringVar(value="Waras (Heirship) Affidavit")
        self.use_ism = tk.BooleanVar(value=False)
        self.preview_font_family = tk.StringVar(value="Mangal")
        self.available_preview_fonts = []
        self.custom_template_path = None
        self.custom_placeholders = []

        # Form Field Registries
        self.field_entries = {}       # key -> CTkEntry or StringVar
        self.heir_entries = []        # list of (name_entry, age_entry, rel_entry)
        self.mined_templates_library = {} # name -> template_path

        # Build Main Interface
        self._create_header_bar()
        self._create_dual_pane_layout()

        # Load Initial Template Form & Sample Data
        self.on_template_change()
        self.fill_sample()

    def _create_header_bar(self):
        """Top Application Bar with Title, Template Selector & Quick Actions."""
        self.top_bar = ctk.CTkFrame(self.root, height=65, corner_radius=0, fg_color="#1E293B")
        self.top_bar.pack(fill="x", side="top")

        # App Brand & Icon
        brand_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        brand_frame.pack(side="left", padx=16, pady=10)

        title = ctk.CTkLabel(
            brand_frame,
            text="📜 Shabana Smart Pratigyapatra",
            font=("Segoe UI", 18, "bold"),
            text_color="#F8FAFC"
        )
        title.pack(anchor="w")

        sub = ctk.CTkLabel(
            brand_frame,
            text="MahaOnline CSC Affidavit & Template Studio",
            font=("Segoe UI", 11),
            text_color="#94A3B8"
        )
        sub.pack(anchor="w")

        # Middle: Template Selector Dropdown
        center_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        center_frame.pack(side="left", padx=30, pady=10)

        ctk.CTkLabel(center_frame, text="निवडा (Template):", font=("Mangal", 12, "bold"), text_color="#E2E8F0").pack(side="left", padx=(0, 8))
        self.template_combo = ctk.CTkComboBox(
            center_frame,
            values=list(TEMPLATES.keys()),
            variable=self.current_template,
            command=self.on_template_change,
            width=260,
            dropdown_font=("Segoe UI", 12)
        )
        self.template_combo.pack(side="left", padx=5)

        # Right Action Buttons
        actions_frame = ctk.CTkFrame(self.top_bar, fg_color="transparent")
        actions_frame.pack(side="right", padx=16, pady=10)

        # Bulk Folder Miner Button (Phase 1 & 2 integration)
        self.bulk_mine_btn = ctk.CTkButton(
            actions_frame,
            text="⚡ Bulk Scan Folder",
            fg_color="#8B5CF6",
            hover_color="#7C3AED",
            font=("Segoe UI", 12, "bold"),
            width=140,
            command=self.open_bulk_scanner_dialog
        )
        self.bulk_mine_btn.pack(side="left", padx=6)

        # Custom Template Load Button
        self.load_doc_btn = ctk.CTkButton(
            actions_frame,
            text="📂 Load Custom DOCX",
            fg_color="#334155",
            hover_color="#475569",
            font=("Segoe UI", 12),
            width=130,
            command=self.load_custom_docx
        )
        self.load_doc_btn.pack(side="left", padx=6)

        # Export Word
        self.export_word_btn = ctk.CTkButton(
            actions_frame,
            text="💾 Export Word",
            fg_color="#10B981",
            hover_color="#059669",
            font=("Segoe UI", 12, "bold"),
            width=110,
            command=self.generate_word
        )
        self.export_word_btn.pack(side="left", padx=6)

    def _create_dual_pane_layout(self):
        """Split screen: Left Form (42% width) & Right Live Document Paper Preview (58% width)."""
        self.split_container = ctk.CTkFrame(self.root, fg_color="#0F172A", corner_radius=0)
        self.split_container.pack(fill="both", expand=True, padx=12, pady=12)

        # Left Column: Inputs & Form
        self.left_pane = ctk.CTkFrame(self.split_container, width=540, corner_radius=12, fg_color="#1E293B")
        self.left_pane.pack(side="left", fill="both", padx=(0, 6), pady=0)
        self.left_pane.pack_propagate(False)

        left_header = ctk.CTkFrame(self.left_pane, height=44, fg_color="#334155", corner_radius=10)
        left_header.pack(fill="x", padx=10, pady=(10, 6))
        ctk.CTkLabel(left_header, text="✏️ माहिती भरा (Form Inputs)", font=("Segoe UI", 13, "bold"), text_color="#F8FAFC").pack(side="left", padx=12)

        # Quick utility row on left
        quick_row = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        quick_row.pack(fill="x", padx=12, pady=4)

        ctk.CTkButton(quick_row, text="Fill Sample", width=85, height=26, font=("Segoe UI", 11),
                      fg_color="#475569", hover_color="#64748B", command=self.fill_sample).pack(side="left", padx=2)
        ctk.CTkButton(quick_row, text="Clear Form", width=85, height=26, font=("Segoe UI", 11),
                      fg_color="#475569", hover_color="#EF4444", command=self.clear_form).pack(side="left", padx=2)
        ctk.CTkButton(quick_row, text="Save JSON", width=85, height=26, font=("Segoe UI", 11),
                      fg_color="#475569", hover_color="#3B82F6", command=self.save_data).pack(side="left", padx=2)
        ctk.CTkButton(quick_row, text="Load JSON", width=85, height=26, font=("Segoe UI", 11),
                      fg_color="#475569", hover_color="#F59E0B", command=self.load_data).pack(side="left", padx=2)

        # ISM Checkbox
        self.ism_chk = ctk.CTkCheckBox(quick_row, text="ISM (DVBW)", variable=self.use_ism, font=("Segoe UI", 11))
        self.ism_chk.pack(side="right", padx=4)

        # Scrollable form container
        self.form_scroll = ctk.CTkScrollableFrame(self.left_pane, corner_radius=8, fg_color="#1E293B")
        self.form_scroll.pack(fill="both", expand=True, padx=6, pady=6)

        # Right Column: Real-time Live Document Preview (A4 paper style)
        self.right_pane = ctk.CTkFrame(self.split_container, corner_radius=12, fg_color="#1E293B")
        self.right_pane.pack(side="right", fill="both", expand=True, padx=(6, 0), pady=0)

        right_header = ctk.CTkFrame(self.right_pane, height=44, fg_color="#334155", corner_radius=10)
        right_header.pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(right_header, text="👁️ थेट दस्तऐवज पूर्वदृश्य (Live A4 Preview)", font=("Segoe UI", 13, "bold"), text_color="#F8FAFC").pack(side="left", padx=12)

        self.zoom_level = tk.IntVar(value=14)
        ctk.CTkButton(right_header, text="A-", width=32, height=26, fg_color="#475569", command=self._zoom_out).pack(side="right", padx=4)
        ctk.CTkButton(right_header, text="A+", width=32, height=26, fg_color="#475569", command=self._zoom_in).pack(side="right", padx=2)
        ctk.CTkLabel(right_header, text="आकार:", font=("Mangal", 11), text_color="#CBD5E1").pack(side="right", padx=4)

        # Select a locally installed Windows font for the preview. Word export
        # retains source document formatting; this selector controls GUI preview.
        try:
            installed = list(tkfont.families(self.root))
        except tk.TclError:
            installed = []
        preferred = ["Mangal", "DVBW Series", "DVBW-TTSurekh", "ISM", "Arial", "Segoe UI"]
        self.available_preview_fonts = sorted(set(installed + preferred), key=str.casefold)
        font_row = ctk.CTkFrame(right_header, fg_color="transparent")
        font_row.pack(side="left", padx=10)
        ctk.CTkLabel(font_row, text="Preview Font:", font=("Segoe UI", 11), text_color="#CBD5E1").pack(side="left", padx=(0, 5))
        self.preview_font_combo = ctk.CTkComboBox(
            font_row, values=self.available_preview_fonts,
            variable=self.preview_font_family, width=190,
            command=self.on_preview_font_change
        )
        self.preview_font_combo.pack(side="left")
        self.font_search_var = tk.StringVar()
        self.font_search_entry = ctk.CTkEntry(
            font_row, textvariable=self.font_search_var, width=150,
            placeholder_text="Type font name…"
        )
        self.font_search_entry.pack(side="left", padx=(6, 0))
        self.font_search_entry.bind("<KeyRelease>", self._filter_preview_fonts)
        self.font_search_entry.bind("<Return>", self._apply_typed_preview_font)

        # A4 Paper Container
        self.paper_frame = ctk.CTkFrame(self.right_pane, corner_radius=8, fg_color="#334155")
        self.paper_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Paper Sheet (White clean canvas for high contrast legal document preview)
        self.preview_text = tk.Text(
            self.paper_frame,
            font=(self.preview_font_family.get(), 14),
            wrap="word",
            bg="#FFFFFF",
            fg="#0F172A",
            padx=32,
            pady=32,
            relief="flat",
            selectbackground="#93C5FD",
            selectforeground="#000000"
        )
        self.preview_text.pack(fill="both", expand=True, padx=8, pady=8)

        # Config text tags for bold/highlight
        self.preview_text.tag_configure("heading", font=(self.preview_font_family.get(), 16, "bold"), justify="center")
        self.preview_text.tag_configure("highlight", background="#FEF08A", foreground="#000000")

    def _filter_preview_fonts(self, event=None):
        """Filter the font dropdown as the user types a family name."""
        query = self.font_search_var.get().strip().casefold()
        matches = [font for font in self.available_preview_fonts if query in font.casefold()]
        self.preview_font_combo.configure(values=matches or self.available_preview_fonts)
        if len(matches) == 1:
            self.preview_font_combo.set(matches[0])

    def _apply_typed_preview_font(self, event=None):
        """Apply a typed font name when it matches an installed family."""
        typed = self.font_search_var.get().strip()
        if not typed:
            return
        exact = next((font for font in self.available_preview_fonts if font.casefold() == typed.casefold()), None)
        partial = [font for font in self.available_preview_fonts if typed.casefold() in font.casefold()]
        selected = exact or (partial[0] if len(partial) == 1 else None)
        if selected:
            self.preview_font_combo.set(selected)
            self._set_preview_font(selected)
        elif partial:
            self.preview_font_combo.configure(values=partial)
            self.preview_font_combo.set(partial[0])

    def on_preview_font_change(self, selected=None):
        """Apply the user's selected installed font to the live text preview."""
        family = (selected or self.preview_font_family.get() or "Mangal").strip()
        self.preview_font_family.set(family)
        size = self.zoom_level.get()
        self.preview_text.configure(font=(family, size))
        self.preview_text.tag_configure("heading", font=(family, size + 2, "bold"))

    def _set_preview_font(self, family):
        """Select a font detected from a loaded DOCX when available."""
        if not family:
            return
        installed = {name.casefold(): name for name in self.available_preview_fonts}
        matched = installed.get(family.casefold(), family)
        self.preview_font_family.set(matched)
        if hasattr(self, "preview_font_combo"):
            self.preview_font_combo.set(matched)
        self.on_preview_font_change(matched)

    def _zoom_in(self):
        sz = self.zoom_level.get() + 1
        if sz <= 24:
            self.zoom_level.set(sz)
            self.on_preview_font_change()

    def _zoom_out(self):
        sz = self.zoom_level.get() - 1
        if sz >= 10:
            self.zoom_level.set(sz)
            self.on_preview_font_change()

    def on_template_change(self, event=None):
        """Build dynamic fields for selected template."""
        for widget in self.form_scroll.winfo_children():
            widget.destroy()

        self.field_entries = {}
        self.heir_entries = []

        template_name = self.current_template.get()
        if template_name in TEMPLATES and TEMPLATES[template_name].get("preview_font_hint"):
            hint = TEMPLATES[template_name]["preview_font_hint"].casefold()
            candidate = next((f for f in self.available_preview_fonts if hint in f.casefold()), None)
            if candidate:
                self._set_preview_font(candidate)

        if template_name in self.mined_templates_library:
            self._build_mined_template_form(template_name)
            return

        if template_name not in TEMPLATES:
            return

        self.mode.set("builtin")
        template_info = TEMPLATES[template_name]
        fields = template_info["fields"]
        has_heirs = template_info.get("heirs", False)

        # Create input cards
        for field in fields:
            card = ctk.CTkFrame(self.form_scroll, fg_color="#0F172A", corner_radius=8)
            card.pack(fill="x", padx=6, pady=4)

            if field == "gender":
                ctk.CTkLabel(card, text="लिंग (Gender):", font=("Mangal", 12, "bold"), text_color="#E2E8F0").pack(anchor="w", padx=10, pady=(6, 2))
                gender_var = tk.StringVar(value="पुरुष")
                r_box = ctk.CTkFrame(card, fg_color="transparent")
                r_box.pack(anchor="w", padx=10, pady=(0, 6))
                ctk.CTkRadioButton(r_box, text="पुरुष", variable=gender_var, value="पुरुष", command=self.update_live_preview).pack(side="left", padx=5)
                ctk.CTkRadioButton(r_box, text="स्त्री", variable=gender_var, value="स्त्री", command=self.update_live_preview).pack(side="left", padx=5)
                self.field_entries[field] = gender_var
            else:
                field_labels = {
                    "applicant_full_name": "अर्जदाराचे पूर्ण नाव",
                    "applicant_age": "वय (वर्षे)",
                    "applicant_occupation": "व्यवसाय",
                    "applicant_village": "गाव",
                    "applicant_address": "पूर्ण पत्ता",
                    "applicant_taluka": "तालुका",
                    "applicant_district": "जिल्हा",
                    "affidavit_place": "ठिकाण",
                    "affidavit_date": "दिनांक",
                    "income_year_range": "उत्पन्नाचे वर्ष",
                    "annual_income": "एकूण वार्षिक उत्पन्न (रु.)",
                }
                label = field_labels.get(field, field.replace("_", " ").title())
                ctk.CTkLabel(card, text=f"{label}:", font=("Mangal", 12), text_color="#CBD5E1").pack(anchor="w", padx=10, pady=(6, 2))
                entry = ctk.CTkEntry(card, height=32, font=("Mangal", 12), fg_color="#1E293B", border_color="#475569")
                entry.pack(fill="x", padx=10, pady=(0, 6))
                entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
                self.field_entries[field] = entry

        # Heirs section if supported
        if has_heirs:
            heir_card = ctk.CTkFrame(self.form_scroll, fg_color="#0F172A", corner_radius=8)
            heir_card.pack(fill="x", padx=6, pady=8)
            ctk.CTkLabel(heir_card, text="👨‍👩‍👧 वारसांचे तपशील (Heir List up to 5):", font=("Mangal", 12, "bold"), text_color="#38BDF8").pack(anchor="w", padx=10, pady=6)

            for i in range(5):
                row = ctk.CTkFrame(heir_card, fg_color="transparent")
                row.pack(fill="x", padx=6, pady=3)
                ctk.CTkLabel(row, text=f"{i+1}.", width=20, text_color="#94A3B8").pack(side="left", padx=2)
                ne = ctk.CTkEntry(row, placeholder_text="नाव (Name)", font=("Mangal", 12), width=160, fg_color="#1E293B")
                ne.pack(side="left", padx=3)
                ae = ctk.CTkEntry(row, placeholder_text="वय", font=("Mangal", 12), width=50, fg_color="#1E293B")
                ae.pack(side="left", padx=3)
                re_entry = ctk.CTkEntry(row, placeholder_text="नाते (Rel)", font=("Mangal", 12), width=90, fg_color="#1E293B")
                re_entry.pack(side="left", padx=3)

                ne.bind("<KeyRelease>", lambda e: self.update_live_preview())
                ae.bind("<KeyRelease>", lambda e: self.update_live_preview())
                re_entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
                self.heir_entries.append((ne, ae, re_entry))

        self.update_live_preview()

    def _build_mined_template_form(self, template_name: str):
        """Build dynamic inputs from placeholders in a loaded DOCX."""
        doc_path = self.mined_templates_library[template_name]
        fields = extract_docx_fields(doc_path)

        info_card = ctk.CTkFrame(self.form_scroll, fg_color="#0F172A", corner_radius=8)
        info_card.pack(fill="x", padx=6, pady=4)
        ctk.CTkLabel(
            info_card,
            text=f"📄 Smart Template: {template_name}  •  {len(fields)} fields detected",
            font=("Segoe UI", 12, "bold"),
            text_color="#A78BFA",
        ).pack(anchor="w", padx=10, pady=6)

        if not fields:
            ctk.CTkLabel(
                self.form_scroll,
                text="या DOCX मध्ये [वय] किंवा {applicant_age} सारखे placeholders आढळले नाहीत.\n"
                     "मजकूरात बदलता येणाऱ्या जागा चौकोनी कंसात [अशी] किंवा curly braces मध्ये {अशी} ठेवा.",
                font=("Mangal", 12),
                text_color="#FBBF24",
                justify="left",
                wraplength=460,
            ).pack(fill="x", padx=10, pady=8)

        for field in fields:
            key = field["key"]
            label = field["label"] or infer_label(key)
            card = ctk.CTkFrame(self.form_scroll, fg_color="#0F172A", corner_radius=8)
            card.pack(fill="x", padx=6, pady=4)

            ctk.CTkLabel(
                card, text=f"{label}:", font=("Mangal", 12), text_color="#CBD5E1"
            ).pack(anchor="w", padx=10, pady=(6, 2))
            entry = ctk.CTkEntry(
                card, height=32, font=("Mangal", 12),
                fg_color="#1E293B", border_color="#475569",
                placeholder_text=key if key != label else "",
            )
            entry.pack(fill="x", padx=10, pady=(0, 6))
            entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
            self.field_entries[key] = entry

        self.update_live_preview()

    def get_current_data(self) -> dict:
        data = {}
        for field, widget in self.field_entries.items():
            if isinstance(widget, ctk.CTkEntry):
                data[field] = widget.get().strip()
            elif isinstance(widget, tk.StringVar):
                data[field] = widget.get()

        template_name = self.current_template.get()
        if template_name in TEMPLATES and TEMPLATES[template_name].get("heirs", False):
            heirs = []
            for name_e, age_e, rel_e in self.heir_entries:
                name = name_e.get().strip()
                age = age_e.get().strip()
                rel = rel_e.get().strip()
                if name or age or rel:
                    heirs.append((name, age, rel))
            data["heirs_list"] = heirs
            lines = [f"{i}) {n} - वय {a} वर्षे - {r}" for i, (n, a, r) in enumerate(heirs, 1)]
            data["heir_table"] = "\n".join(lines) if lines else "कोणीही वारस नाही"
            data["number_of_heirs"] = str(len(heirs))

        return data

    def update_live_preview(self):
        """Real-time reactive live preview rendering."""
        template_name = self.current_template.get()
        data = self.get_current_data()

        self.preview_text.delete("1.0", "end")

        if template_name in self.mined_templates_library:
            doc_path = self.mined_templates_library[template_name]
            try:
                self.preview_text.insert("1.0", build_docx_preview(doc_path, data))
            except Exception as ex:
                self.preview_text.insert("1.0", f"Preview Error: {ex}")
            return

        if template_name not in TEMPLATES:
            return

        template_info = TEMPLATES[template_name]
        stamp_guide = ""
        if template_info.get("preview_font_hint"):
            # Screen-only guide; the exported DOCX reserves blank stamp space.
            stamp_guide = (
                "┌────────────────────────────┐\n"
                "│     ₹500 STAMP PAPER       │\n"
                "│      PREVIEW GUIDE ONLY    │\n"
                "│  FINAL DOCUMENT: BLANK     │\n"
                "└────────────────────────────┘\n\n"
            )
        if "gender" in data:
            data["gender_verb"] = "सांगतो" if data["gender"] == "पुरुष" else "सांगते"
            data["gender_prefix"] = "श्री" if data["gender"] == "पुरुष" else "सौ."

        # Income Certificate 3 years calculations
        if template_name == "Income Certificate (3 Years)":
            def to_int(v):
                digits = re.sub(r"[^\d]", "", v)
                return int(digits) if digits else 0
            for i in (1, 2, 3):
                t = (to_int(data.get(f"income{i}_salary", "0")) +
                     to_int(data.get(f"income{i}_agri", "0")) +
                     to_int(data.get(f"income{i}_labour", "0")) +
                     to_int(data.get(f"income{i}_other", "0")))
                data[f"total{i}"] = f"{t}/-"

        try:
            # Format preview text safely
            filled = template_info["template"].format(**data)
            self.preview_text.insert("1.0", stamp_guide + filled)
            if stamp_guide:
                self.preview_text.tag_configure("stamp_guide", justify="center", foreground="#64748B")
                self.preview_text.tag_add("stamp_guide", "1.0", "7.0")
        except KeyError as missing:
            # Fallback for partially filled fields
            safe_data = {k: (data.get(k) or f"[{k}]") for k in template_info["fields"]}
            safe_data.update(data)
            try:
                filled = template_info["template"].format(**safe_data)
                self.preview_text.insert("1.0", stamp_guide + filled)
                if stamp_guide:
                    self.preview_text.tag_configure("stamp_guide", justify="center", foreground="#64748B")
                    self.preview_text.tag_add("stamp_guide", "1.0", "7.0")
            except Exception:
                self.preview_text.insert("1.0", template_info["template"])

    def fill_sample(self):
        """Populate current template with authentic Marathi sample data."""
        template_name = self.current_template.get()
        if template_name not in TEMPLATES:
            return

        sample = {
            "applicant_full_name": "राम शंकर जोशी",
            "applicant_age": "45",
            "applicant_occupation": "शिक्षक",
            "applicant_taluka": "पुणे",
            "applicant_district": "पुणे",
            "applicant_address": "रा. शनिवार पेठ, पुणे",
            "deceased_relation": "वडील",
            "deceased_name": "शंकर राम जोशी",
            "deceased_death_date": "१५/०८/२०२३",
            "deceased_death_place": "पुणे",
            "city_survey_number": "गट क्र. १२३, ह. नं. ४५",
            "affidavit_place": "पुणे",
            "affidavit_date": "०१/०४/२०२५",
            "gender": "पुरुष",
            "old_name": "सुनिल कुमार शर्मा",
            "new_name": "सुनिल कुमार",
            "reason": "धार्मिक कारणास्तव",
            "document_type": "मार्कशीट",
            "document_details": "SSC गुणपत्रिका क्र. 123",
            "lost_date": "१०/०२/२०२५",
            "lost_place": "पुणे स्टेशन",
            "complaint_filed": "होय, नोंद क्र. 456/25",
        }

        for k, val in sample.items():
            if k in self.field_entries:
                w = self.field_entries[k]
                if isinstance(w, ctk.CTkEntry):
                    w.delete(0, "end")
                    w.insert(0, val)
                elif isinstance(w, tk.StringVar):
                    w.set(val)

        # Fill heirs sample
        if self.heir_entries:
            heir_samples = [("राम शंकर जोशी", "45", "पुत्र"), ("सीता शंकर जोशी", "40", "पत्नी")]
            for idx, (n_e, a_e, r_e) in enumerate(self.heir_entries):
                n_e.delete(0, "end")
                a_e.delete(0, "end")
                r_e.delete(0, "end")
                if idx < len(heir_samples):
                    n, a, r = heir_samples[idx]
                    n_e.insert(0, n); a_e.insert(0, a); r_e.insert(0, r)

        self.update_live_preview()

    def clear_form(self):
        for w in self.field_entries.values():
            if isinstance(w, ctk.CTkEntry):
                w.delete(0, "end")
        for ne, ae, re_entry in self.heir_entries:
            ne.delete(0, "end"); ae.delete(0, "end"); re_entry.delete(0, "end")
        self.update_live_preview()

    def generate_word(self):
        """Export completed document to Word (.docx) with Marathi Unicode / ISM."""
        template_name = self.current_template.get()
        data = self.get_current_data()

        filename = filedialog.asksaveasfilename(
            defaultextension=".docx",
            filetypes=[("Word Document", "*.docx")],
            initialfile=f"{template_name.replace(' ', '_')}.docx"
        )
        if not filename:
            return

        try:
            if template_name in self.mined_templates_library:
                create_filled_document(self.mined_templates_library[template_name], data, filename)
            else:
                filled_text = self.preview_text.get("1.0", "end").strip()
                taluka = data.get("applicant_taluka", "")
                if TEMPLATES[template_name].get("preview_font_hint"):
                    # The DVBW sample is already legacy-encoded; do not pass it
                    # through Unicode-to-ISM conversion a second time.
                    export_legacy_text_docx(
                        filled_text, filename, self.preview_font_family.get()
                    )
                else:
                    export_to_docx(filled_text, filename, barcode_data=None, taluka_name=taluka, use_ism=self.use_ism.get())
            messagebox.showinfo("यशस्वी (Success)", f"दस्तऐवज सेव्ह करण्यात आला आहे:\n{filename}")
        except Exception as e:
            messagebox.showerror("त्रुटी (Error)", f"Word फाइल तयार करताना त्रुटी आली:\n{e}")

    def load_custom_docx(self):
        """Mine placeholders from any single DOCX and add to studio."""
        file_path = filedialog.askopenfilename(filetypes=[("Word files", "*.docx")])
        if not file_path:
            return
        try:
            name = Path(file_path).stem.replace("_", " ").title()
            detected = extract_docx_fields(file_path)
            detected_font = detect_docx_font_family(file_path)
            if not detected:
                proceed = messagebox.askyesno(
                    "Placeholders आढळले नाहीत",
                    "या DOCX मध्ये [वय] किंवा {applicant_age} सारखे placeholders सापडले नाहीत.\n\n"
                    "फाइल लोड करू का? नंतर form fields दिसणार नाहीत, जोपर्यंत placeholders जोडले जात नाहीत."
                )
                if not proceed:
                    return
            self.mined_templates_library[name] = file_path
            current_vals = list(self.template_combo.cget("values"))
            if name not in current_vals:
                current_vals.append(name)
                self.template_combo.configure(values=current_vals)
            self.current_template.set(name)
            self.on_template_change()
            if detected_font:
                self._set_preview_font(detected_font)
            messagebox.showinfo("यशस्वी", f"कस्टम टेम्पलेट लोड झाले: {name}")
        except Exception as e:
            messagebox.showerror("त्रुटी", f"टेम्पलेट लोड करताना त्रुटी आली: {e}")

    def open_bulk_scanner_dialog(self):
        """Open Folder Mining and Deduplication Dialog (Phase 1, 2, 4)."""
        folder = filedialog.askdirectory(title="निवडा: ज्या फोल्डरमधील DOCX स्कॅन करायचे आहेत")
        if not folder:
            return

        out_folder = Path(folder) / "Mined_Templates"
        report = process_template_folder(folder, out_folder)

        # Register newly mined templates into the studio dropdown
        current_vals = list(self.template_combo.cget("values"))
        new_count = 0
        for t in report.templates:
            name = f"⭐ {t['name']}"
            self.mined_templates_library[name] = t["template_docx"]
            if name not in current_vals:
                current_vals.append(name)
                new_count += 1

        self.template_combo.configure(values=current_vals)

        msg = (
            f"✅ फोल्डर स्कॅनिंग यशस्वीपणे पूर्ण झाले!\n\n"
            f"• एकूण स्कॅन केलेल्या फाइल्स: {report.total_scanned}\n"
            f"• नवीन युनिक टेम्पलेट्स: {report.unique_mined}\n"
            f"• वगळलेले डुप्लिकेट (Duplicates Skipped): {report.duplicates_skipped}\n"
            f"• एकाच फाइलमधील व्यक्ती रिपीट्स कॉम्प्रेश केले: {report.repeated_sections_compressed}\n\n"
            f"सर्व टेम्पलेट्स स्टुडिओमध्ये लोड करण्यात आले आहेत!"
        )
        messagebox.showinfo("बल्क स्कॅनर रिपोर्ट (Scan Report)", msg)

    def save_data(self):
        data = self.get_current_data()
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("यशस्वी", f"माहिती सेव्ह झाली: {filename}")

    def load_data(self):
        filename = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if not filename:
            return
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
            for k, val in data.items():
                if k in self.field_entries:
                    w = self.field_entries[k]
                    if isinstance(w, ctk.CTkEntry):
                        w.delete(0, "end"); w.insert(0, str(val))
                    elif isinstance(w, tk.StringVar):
                        w.set(str(val))
            self.update_live_preview()
            messagebox.showinfo("यशस्वी", "माहिती लोड झाली!")
        except Exception as e:
            messagebox.showerror("त्रुटी", f"डेटा लोड करताना त्रुटी आली: {e}")


if __name__ == "__main__":
    app = AffidavitStudio()
    app.root.mainloop()