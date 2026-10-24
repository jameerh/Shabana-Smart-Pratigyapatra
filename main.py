# main.py
"""Shabana Smart Pratigyapatra (शबाना स्मार्ट प्रतिज्ञापत्र) - Affidavit Master
Complete Dual-Pane Live Preview Studio & Bulk Bold Template Generator
"""
import json
import io
import os
import re
import sys
import tempfile
import tkinter as tk
import tkinter.font as tkfont
from pathlib import Path
from PIL import Image, ImageTk
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from templates import TEMPLATES
from docx_export import export_to_docx, export_legacy_text_docx, ISM_AVAILABLE, unicode_to_ism
from engine.docx_preview_renderer import render_docx_pages, convert_docx_to_pdf, PreviewRenderError
from engine.workspace_services import save_applicant_profile, load_applicant_profile, snapshot_template, list_template_snapshots, compare_text_documents
from template_parser import extract_placeholders, create_filled_document
from engine.smart_docx_import import extract_docx_fields, infer_label, build_docx_preview, detect_docx_font_family
from engine.form_history import append_form_history, history_suggestions, validate_mobile, validate_date
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
        self.history_file = Path.home() / 'Documents' / 'Shabana Smart Pratigyapatra' / 'form_history.json'
        self.stamp_width_var = tk.StringVar(value='2.0')
        self.stamp_height_var = tk.StringVar(value='2.0')
        self._preview_after_id = None
        self._preview_image_refs = []
        self._preview_pages_frame = None
        self._preview_canvas = None
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
        self.template_search_var = tk.StringVar()
        self.template_search_entry = ctk.CTkEntry(center_frame, textvariable=self.template_search_var, width=170, placeholder_text="Search templates…")
        self.template_search_entry.pack(side="left", padx=(5, 2))
        self.template_search_entry.bind("<KeyRelease>", self._filter_templates)
        self.template_search_entry.bind("<Return>", self._choose_first_template_match)
        self.template_combo = ctk.CTkComboBox(
            center_frame, values=list(TEMPLATES.keys()), variable=self.current_template,
            command=self.on_template_change, width=260, dropdown_font=("Segoe UI", 12)
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

        profile_row = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        profile_row.pack(fill="x", padx=12, pady=(0, 4))
        ctk.CTkButton(
            profile_row, text="Save Applicant Profile", width=145, height=26,
            font=("Segoe UI", 11), fg_color="#475569",
            command=self.save_applicant_profile_dialog
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            profile_row, text="Load Applicant Profile", width=145, height=26,
            font=("Segoe UI", 11), fg_color="#475569",
            command=self.load_applicant_profile_dialog
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            profile_row, text="Template History", width=112, height=26,
            font=("Segoe UI", 11), fg_color="#475569",
            command=self.browse_template_history
        ).pack(side="left", padx=2)
        ctk.CTkButton(
            profile_row, text="Compare DOCX", width=100, height=26,
            font=("Segoe UI", 11), fg_color="#475569",
            command=self.compare_with_docx
        ).pack(side="left", padx=2)

        ctk.CTkButton(profile_row, text="Random Test Data", width=125, height=26, font=("Segoe UI", 11), fg_color="#0F766E", command=self.fill_random_test_data).pack(side="left", padx=2)

        stamp_row = ctk.CTkFrame(self.left_pane, fg_color="transparent")
        stamp_row.pack(fill="x", padx=12, pady=(0, 5))
        ctk.CTkLabel(stamp_row, text="Stamp area (in):", font=("Segoe UI", 10)).pack(side="left", padx=(0, 5))
        ctk.CTkLabel(stamp_row, text="W").pack(side="left")
        ctk.CTkEntry(stamp_row, textvariable=self.stamp_width_var, width=55, height=25).pack(side="left", padx=3)
        ctk.CTkLabel(stamp_row, text="H").pack(side="left")
        ctk.CTkEntry(stamp_row, textvariable=self.stamp_height_var, width=55, height=25).pack(side="left", padx=3)
        ctk.CTkLabel(stamp_row, text="Default 2 × 2 in; confirm local requirements", font=("Segoe UI", 9), text_color="#94A3B8").pack(side="left", padx=5)

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
        ctk.CTkButton(
            font_row, text="Export PDF", width=86, height=28,
            fg_color="#0F766E", hover_color="#115E59",
            command=self.export_pdf
        ).pack(side="left", padx=(8, 0))
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

        # Page-image surface for a Word-like preview. Text remains as fallback
        # when LibreOffice or PyMuPDF is not installed.
        self.preview_pages_container = ctk.CTkFrame(self.paper_frame, fg_color="#334155")
        self.preview_canvas = tk.Canvas(self.preview_pages_container, bg="#334155", highlightthickness=0)
        self.preview_scrollbar = ttk.Scrollbar(self.preview_pages_container, orient="vertical", command=self.preview_canvas.yview)
        self.preview_canvas.configure(yscrollcommand=self.preview_scrollbar.set)
        self.preview_scrollbar.pack(side="right", fill="y")
        self.preview_canvas.pack(side="left", fill="both", expand=True)
        self.preview_pages_inner = tk.Frame(self.preview_canvas, bg="#334155")
        self.preview_canvas_window = self.preview_canvas.create_window((0, 0), window=self.preview_pages_inner, anchor="nw")
        self.preview_pages_inner.bind("<Configure>", lambda e: self.preview_canvas.configure(scrollregion=self.preview_canvas.bbox("all")))
        self.preview_canvas.bind("<Configure>", lambda e: self.preview_canvas.itemconfigure(self.preview_canvas_window, width=e.width))

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
            self.font_search_var.set(selected)
            self._set_preview_font(selected)
        elif partial:
            prefix = [font for font in partial if font.casefold().startswith(typed.casefold())]
            candidate = prefix[0] if prefix else partial[0]
            self.preview_font_combo.configure(values=partial)
            self.preview_font_combo.set(candidate)
            self._set_preview_font(candidate)
            self.font_search_var.set(candidate)

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

    def _history_autocomplete(self, event, widget, field_key):
        """Filter saved cross-template values while preserving free typing."""
        query = widget.get().strip().casefold()
        values = history_suggestions(self.history_file, field_key, limit=100)
        matches = [value for value in values if query in value.casefold()] if query else values
        widget.configure(values=matches[:30])
        self.update_live_preview()

    def open_date_picker(self, widget):
        """Open a calendar popup; gracefully explain if tkcalendar isn't installed."""
        try:
            from tkcalendar import Calendar
        except ImportError:
            messagebox.showwarning("Calendar unavailable", "Install the calendar dependency with: pip install tkcalendar")
            return
        popup = ctk.CTkToplevel(self.root)
        popup.title("Select date")
        popup.geometry("320x300")
        popup.transient(self.root)
        calendar = Calendar(popup, date_pattern="dd/mm/yyyy")
        calendar.pack(fill="both", expand=True, padx=10, pady=10)
        def choose():
            widget.delete(0, "end")
            widget.insert(0, calendar.get_date())
            popup.destroy()
            self.update_live_preview()
        ctk.CTkButton(popup, text="Use selected date", command=choose).pack(pady=(0, 10))

    def _filter_templates(self, event=None):
        query = self.template_search_var.get().strip().casefold()
        names = list(TEMPLATES.keys()) + list(self.mined_templates_library.keys())
        matches = [name for name in names if query in name.casefold()] if query else names
        self.template_combo.configure(values=matches or names)
        if len(matches) == 1:
            self.template_combo.set(matches[0])

    def _choose_first_template_match(self, event=None):
        values = list(self.template_combo.cget("values"))
        if values:
            chosen = values[0]
            self.template_combo.set(chosen)
            self.current_template.set(chosen)
            self.on_template_change()

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
                suggestions = history_suggestions(self.history_file, field, limit=30) if ("name" in field or "mobile" in field or "phone" in field) else []
                if ("name" in field or "mobile" in field or "phone" in field):
                    entry = ttk.Combobox(card, values=suggestions, font=("Mangal", 12))
                    entry.configure(state="normal")
                    entry.pack(fill="x", padx=10, pady=(0, 6))
                    entry.bind("<KeyRelease>", lambda e, w=entry, k=field: self._history_autocomplete(e, w, k))
                else:
                    entry = ctk.CTkEntry(card, height=32, font=("Mangal", 12), fg_color="#1E293B", border_color="#475569")
                    entry.pack(fill="x", padx=10, pady=(0, 6))
                entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
                self.field_entries[field] = entry
                if "date" in field:
                    ctk.CTkButton(card, text="📅 Calendar", width=95, height=26, command=lambda w=entry: self.open_date_picker(w)).pack(anchor="e", padx=10, pady=(0, 6))

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
            suggestions = history_suggestions(self.history_file, key, limit=30) if ("name" in key or "mobile" in key or "phone" in key) else []
            if ("name" in key or "mobile" in key or "phone" in key):
                entry = ttk.Combobox(card, values=suggestions, font=("Mangal", 12))
                entry.configure(state="normal")
                entry.pack(fill="x", padx=10, pady=(0, 6))
                entry.bind("<KeyRelease>", lambda e, w=entry, k=key: self._history_autocomplete(e, w, k))
            else:
                entry = ctk.CTkEntry(
                    card, height=32, font=("Mangal", 12),
                    fg_color="#1E293B", border_color="#475569",
                    placeholder_text=key if key != label else "",
                )
                entry.pack(fill="x", padx=10, pady=(0, 6))
            entry.bind("<KeyRelease>", lambda e: self.update_live_preview())
            self.field_entries[key] = entry
            if "date" in key:
                ctk.CTkButton(card, text="📅 Calendar", width=95, height=26, command=lambda w=entry: self.open_date_picker(w)).pack(anchor="e", padx=10, pady=(0, 6))

        self.update_live_preview()

    def get_current_data(self) -> dict:
        data = {}
        for field, widget in self.field_entries.items():
            # Imported templates use ttk.Combobox for name/mobile fields so
            # history autocomplete can work. Read those values just like entries;
            # otherwise their placeholders remain unfilled in preview/export.
            if isinstance(widget, (ctk.CTkEntry, ttk.Combobox)):
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

    def _schedule_wysiwyg_preview(self):
        """Debounce document rendering so rapid typing does not launch many processes."""
        if self._preview_after_id:
            try:
                self.root.after_cancel(self._preview_after_id)
            except tk.TclError:
                pass
        self._preview_after_id = self.root.after(850, self._render_wysiwyg_preview)

    def _render_wysiwyg_preview(self):
        """Render the same kind of DOCX that export creates, then display its pages."""
        self._preview_after_id = None
        template_name = self.current_template.get()
        data = self.get_current_data()
        temp_dir = tempfile.TemporaryDirectory(prefix="shabana_live_docx_")
        path = Path(temp_dir.name) / "live_preview.docx"
        try:
            if template_name in self.mined_templates_library:
                create_filled_document(self.mined_templates_library[template_name], data, path)
            elif template_name in TEMPLATES:
                info = TEMPLATES[template_name]
                filled_text = self.preview_text.get("1.0", "end-1c")
                # The stamp guide is only a UI hint and must never be exported.
                filled_text = re.sub(
                    r"^┌─+┐\n│     ₹500 STAMP PAPER       │\n│      PREVIEW GUIDE ONLY    │\n│  FINAL DOCUMENT: BLANK     │\n└─+┘\n\n",
                    "", filled_text
                )
                if info.get("preview_font_hint"):
                    export_legacy_text_docx(filled_text, path, self.preview_font_family.get(), include_stamp_preview=True, stamp_width=self.get_stamp_dimensions()[0], stamp_height=self.get_stamp_dimensions()[1])
                else:
                    export_to_docx(
                        filled_text, str(path), barcode_data=None,
                        taluka_name=data.get("applicant_taluka", ""),
                        use_ism=self.use_ism.get(), stamp_width=self.get_stamp_dimensions()[0], stamp_height=self.get_stamp_dimensions()[1]
                    )
            else:
                temp_dir.cleanup()
                return
            page_pngs = render_docx_pages(path)
            self._show_rendered_preview(page_pngs)
        except Exception as exc:
            # Always fall back cleanly if rendering fails, including after a
            # previously successful render.
            self.preview_pages_container.pack_forget()
            self.preview_text.pack(fill="both", expand=True, padx=8, pady=8)
            self._set_preview_status(f"Word-page preview unavailable: {exc}")
        finally:
            temp_dir.cleanup()

    def _show_rendered_preview(self, page_pngs):
        """Display all rendered pages as scaled images in a vertically scrollable pane."""
        for widget in self.preview_pages_inner.winfo_children():
            widget.destroy()
        self._preview_image_refs = []
        available_width = max(400, self.preview_canvas.winfo_width() - 36)
        for index, png in enumerate(page_pngs, start=1):
            image = Image.open(io.BytesIO(png)).convert("RGB")
            scale = min(1.0, available_width / image.width)
            if scale < 1:
                image = image.resize((int(image.width * scale), int(image.height * scale)), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(image)
            self._preview_image_refs.append(photo)
            label = tk.Label(self.preview_pages_inner, image=photo, bg="#334155", bd=0)
            label.pack(padx=12, pady=(12, 3))
            tk.Label(self.preview_pages_inner, text=f"Page {index} of {len(page_pngs)}", bg="#334155", fg="#CBD5E1").pack(pady=(0, 12))
        self.preview_text.pack_forget()
        self.preview_pages_container.pack(fill="both", expand=True, padx=8, pady=8)
        self._set_preview_status(f"Rendered document preview • {len(page_pngs)} page(s)")

    def _set_preview_status(self, message):
        """Display current preview renderer status in the window title."""
        base = "Shabana Smart Pratigyapatra (Affidavit Master) - Maharashtra"
        self.root.title(f"{base} | {message}")

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
            self._schedule_wysiwyg_preview()
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

        # Legacy DVBW templates contain legacy-encoded static text. Convert only
        # Unicode values entered in the form, not the template body itself.
        format_data = dict(data)
        if template_info.get("preview_font_hint") and ISM_AVAILABLE:
            for field in template_info.get("fields", []):
                value = format_data.get(field)
                if isinstance(value, str) and value:
                    format_data[field] = unicode_to_ism(value)

        try:
            # Format preview text safely
            filled = template_info["template"].format(**format_data)
            self.preview_text.insert("1.0", stamp_guide + filled)
            if stamp_guide:
                self.preview_text.tag_configure("stamp_guide", justify="center", foreground="#64748B")
                self.preview_text.tag_add("stamp_guide", "1.0", "7.0")
        except KeyError as missing:
            # Fallback for partially filled fields
            safe_data = {k: (data.get(k) or f"[{k}]") for k in template_info["fields"]}
            safe_data.update(data)
            try:
                filled = template_info["template"].format(**{**safe_data, **format_data})
                self.preview_text.insert("1.0", stamp_guide + filled)
                if stamp_guide:
                    self.preview_text.tag_configure("stamp_guide", justify="center", foreground="#64748B")
                    self.preview_text.tag_add("stamp_guide", "1.0", "7.0")
            except Exception:
                self.preview_text.insert("1.0", template_info["template"])

        self._schedule_wysiwyg_preview()

    def fill_random_test_data(self):
        """Fill the active form with synthetic values for rapid preview/export tests."""
        import random
        first = ["राम", "सीता", "अमोल", "पूजा", "सचिन", "प्रिया"]
        last = ["पाटील", "जाधव", "शिंदे", "देशमुख", "मोरे"]
        places = ["जत", "सांगली", "पुणे", "मिरज", "कवठेमहांकाळ"]
        today = __import__("datetime").date.today().strftime("%d/%m/%Y")
        for key, widget in self.field_entries.items():
            if isinstance(widget, tk.StringVar):
                widget.set(random.choice(["पुरुष", "स्त्री"]))
                continue
            if not hasattr(widget, "delete"):
                continue
            if "name" in key:
                value = f"{random.choice(first)} {random.choice(last)}"
            elif "mobile" in key or "phone" in key:
                value = "9" + "".join(random.choice("0123456789") for _ in range(9))
            elif "age" in key:
                value = str(random.randint(21, 65))
            elif "date" in key:
                value = today
            elif "occupation" in key:
                value = random.choice(["शेती", "व्यवसाय", "शिक्षक", "मजुरी"])
            elif any(token in key for token in ("village", "taluka", "district", "place", "office")):
                value = random.choice(places)
            elif "percentage" in key:
                value = random.choice(["1.3%", "2.0%", "5%"])
            elif "property" in key or "survey" in key:
                value = f"{random.randint(100, 999)}/{random.randint(1, 9)}"
            elif "income" in key:
                value = str(random.choice([120000, 180000, 240000, 360000]))
            else:
                value = f"TEST-{random.randint(100, 999)}"
            widget.delete(0, "end")
            widget.insert(0, value)
        for row in self.heir_entries:
            values = [f"{random.choice(first)} {random.choice(last)}", str(random.randint(18, 70)), random.choice(["पुत्र", "पत्नी", "मुलगी"])]
            for widget, value in zip(row, values):
                widget.delete(0, "end"); widget.insert(0, value)
        self.update_live_preview()

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
            if hasattr(w, "delete"):
                w.delete(0, "end")
        for ne, ae, re_entry in self.heir_entries:
            ne.delete(0, "end"); ae.delete(0, "end"); re_entry.delete(0, "end")
        self.update_live_preview()

    def get_stamp_dimensions(self):
        """Return validated configurable stamp area dimensions in inches."""
        try:
            width, height = float(self.stamp_width_var.get()), float(self.stamp_height_var.get())
        except (ValueError, TypeError):
            raise ValueError("Stamp width and height must be numeric inches.")
        if not (0.5 <= width <= 6.0 and 0.5 <= height <= 8.0):
            raise ValueError("Stamp dimensions must be width 0.5–6.0 in and height 0.5–8.0 in.")
        return width, height

    def generate_word(self):
        """Export completed document to Word (.docx) with Marathi Unicode / ISM."""
        template_name = self.current_template.get()
        data = self.get_current_data()
        template_info = TEMPLATES.get(template_name, {})
        for key, value in data.items():
            if ("mobile" in key.casefold() or "phone" in key.casefold()) and not validate_mobile(value):
                messagebox.showwarning("Invalid mobile number", f"{key}: enter a valid 10-digit Indian mobile number.")
                return
            if "date" in key.casefold() and value and not validate_date(value):
                messagebox.showwarning("Invalid date", f"{key}: use DD/MM/YYYY format or choose from the calendar.")
                return
        required = template_info.get("required_fields", [])
        missing = [field for field in required if not str(data.get(field, "")).strip()]
        if missing:
            labels = {
                "applicant_full_name": "अर्जदाराचे पूर्ण नाव",
                "applicant_age": "वय",
                "applicant_occupation": "व्यवसाय",
                "applicant_village": "गाव",
                "property_number": "मालमत्ता / गट क्रमांक",
                "connection_percentage": "कनेक्शन टक्केवारी",
                "electricity_office": "वीज कार्यालय",
                "affidavit_place": "ठिकाण",
                "affidavit_date": "दिनांक",
            }
            messagebox.showwarning(
                "माहिती अपूर्ण",
                "कृपया निर्यात करण्यापूर्वी ही माहिती भरा:\n\n"
                + "\n".join("• " + labels.get(field, field) for field in missing)
            )
            return

        try:
            stamp_width, stamp_height = self.get_stamp_dimensions()
        except ValueError as exc:
            messagebox.showwarning("Invalid stamp dimensions", str(exc))
            return

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
                # Remove the UI-only stamp guide; the final DOCX reserves a blank area.
                filled_text = re.sub(
                    r"^┌─+┐\n│     ₹500 STAMP PAPER       │\n│      PREVIEW GUIDE ONLY    │\n│  FINAL DOCUMENT: BLANK     │\n└─+┘\n\n",
                    "", filled_text
                )
                taluka = data.get("applicant_taluka", "")
                if TEMPLATES[template_name].get("preview_font_hint"):
                    # The DVBW sample is already legacy-encoded; do not pass it
                    # through Unicode-to-ISM conversion a second time.
                    export_legacy_text_docx(
                        filled_text, filename, self.preview_font_family.get(), stamp_width=stamp_width, stamp_height=stamp_height
                    )
                else:
                    export_to_docx(filled_text, filename, barcode_data=None, taluka_name=taluka, use_ism=self.use_ism.get(), stamp_width=stamp_width, stamp_height=stamp_height)
            try:
                append_form_history(self.history_file, template_name, data)
            except Exception as history_error:
                messagebox.showwarning("History warning", f"Document exported, but history could not be saved: {history_error}")
            messagebox.showinfo("यशस्वी (Success)", f"दस्तऐवज सेव्ह करण्यात आला आहे:\n{filename}")
        except Exception as e:
            messagebox.showerror("त्रुटी (Error)", f"Word फाइल तयार करताना त्रुटी आली:\n{e}")

    def export_pdf(self):
        """Export the current document as PDF through the local DOCX renderer."""
        template_name = self.current_template.get()
        filename = filedialog.asksaveasfilename(
            defaultextension=".pdf", filetypes=[("PDF document", "*.pdf")],
            initialfile=f"{template_name.replace(' ', '_')}.pdf"
        )
        if not filename:
            return
        temp_dir = tempfile.TemporaryDirectory(prefix="shabana_pdf_export_")
        docx_path = Path(temp_dir.name) / "export.docx"
        try:
            data = self.get_current_data()
            if template_name in self.mined_templates_library:
                create_filled_document(self.mined_templates_library[template_name], data, docx_path)
            elif template_name in TEMPLATES:
                text = self.preview_text.get("1.0", "end-1c")
                text = re.sub(
                    r"^┌─+┐\n│     ₹500 STAMP PAPER       │\n│      PREVIEW GUIDE ONLY    │\n│  FINAL DOCUMENT: BLANK     │\n└─+┘\n\n",
                    "", text
                )
                if TEMPLATES[template_name].get("preview_font_hint"):
                    export_legacy_text_docx(text, docx_path, self.preview_font_family.get(), stamp_width=self.get_stamp_dimensions()[0], stamp_height=self.get_stamp_dimensions()[1])
                else:
                    export_to_docx(text, str(docx_path), barcode_data=None,
                                   taluka_name=data.get("applicant_taluka", ""),
                                   use_ism=self.use_ism.get(), stamp_width=self.get_stamp_dimensions()[0], stamp_height=self.get_stamp_dimensions()[1])
            else:
                return
            output = convert_docx_to_pdf(docx_path, filename)
            messagebox.showinfo("PDF export", f"PDF saved successfully:\n{output}")
        except Exception as exc:
            messagebox.showerror("PDF export failed", str(exc))
        finally:
            temp_dir.cleanup()

    def load_custom_docx(self):
        """Mine placeholders from any single DOCX and add to studio."""
        file_path = filedialog.askopenfilename(filetypes=[("Word files", "*.docx")])
        if not file_path:
            return
        try:
            name = Path(file_path).stem.replace("_", " ").title()
            history_dir = Path.home() / "Documents" / "Shabana Smart Pratigyapatra" / "template_history"
            snapshot_template(file_path, history_dir, name)
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

    def browse_template_history(self):
        """Open an archived copy of an imported template from local history."""
        history_root = Path.home() / "Documents" / "Shabana Smart Pratigyapatra" / "template_history"
        selected = filedialog.askopenfilename(
            title="Select an archived DOCX template",
            initialdir=str(history_root) if history_root.exists() else str(Path.home() / "Documents"),
            filetypes=[("Word documents", "*.docx")],
        )
        if selected:
            # Load the archived copy through the normal import/placeholder pipeline.
            self.mined_templates_library[Path(selected).stem] = selected
            names = list(self.template_combo.cget("values"))
            if Path(selected).stem not in names:
                names.append(Path(selected).stem)
                self.template_combo.configure(values=names)
            self.current_template.set(Path(selected).stem)
            self.on_template_change()
            detected = detect_docx_font_family(selected)
            if detected:
                self._set_preview_font(detected)

    def compare_with_docx(self):
        """Show a line-level text comparison against a selected reference DOCX."""
        selected = filedialog.askopenfilename(
            title="Select reference DOCX for comparison",
            filetypes=[("Word documents", "*.docx")],
        )
        if not selected:
            return
        try:
            reference = build_docx_preview(selected, {})
            current = self.preview_text.get("1.0", "end-1c")
            result = compare_text_documents(reference, current)
            window = ctk.CTkToplevel(self.root)
            window.title("Document Text Comparison")
            window.geometry("900x620")
            ctk.CTkLabel(
                window,
                text=f"Line-level text similarity: {result['similarity_percent']}%  •  "
                     f"+{len(result['added_lines'])} added / -{len(result['removed_lines'])} removed",
                font=("Segoe UI", 13, "bold"),
            ).pack(fill="x", padx=12, pady=10)
            diff_box = ctk.CTkTextbox(window, wrap="none", font=("Consolas", 11))
            diff_box.pack(fill="both", expand=True, padx=12, pady=(0, 12))
            diff_box.insert("1.0", result["unified_diff"] or "No text differences found.")
            diff_box.configure(state="disabled")
        except Exception as exc:
            messagebox.showerror("Comparison failed", str(exc))

    def save_applicant_profile_dialog(self):
        """Save reusable applicant details locally as a named profile."""
        name = ctk.CTkInputDialog(title="Applicant Profile", text="Profile name:").get_input()
        if not name or not name.strip():
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".json", initialfile=name.strip().replace(" ", "_") + ".json",
            filetypes=[("Applicant profile", "*.json")]
        )
        if not filename:
            return
        try:
            save_applicant_profile(Path(filename).parent, Path(filename).stem, self.get_current_data())
            messagebox.showinfo("Profile saved", f"Applicant profile saved locally:\n{filename}")
        except Exception as exc:
            messagebox.showerror("Profile error", str(exc))

    def load_applicant_profile_dialog(self):
        """Load saved profile values into matching current form fields."""
        filename = filedialog.askopenfilename(filetypes=[("Applicant profile", "*.json")])
        if not filename:
            return
        try:
            data = load_applicant_profile(filename)
            for key, value in data.items():
                widget = self.field_entries.get(key)
                if isinstance(widget, ctk.CTkEntry):
                    widget.delete(0, "end")
                    widget.insert(0, value)
                elif isinstance(widget, tk.StringVar):
                    widget.set(value)
            self.update_live_preview()
            messagebox.showinfo("Profile loaded", "Matching fields have been filled.")
        except Exception as exc:
            messagebox.showerror("Profile error", str(exc))

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