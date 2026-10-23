# template_parser.py
import re
from docx import Document
from docx.shared import Pt

def extract_placeholders(docx_path):
    """
    Extract all unique placeholders from a Word document.
    Placeholders are strings like {field_name} (case-sensitive).
    """
    doc = Document(docx_path)
    placeholders = set()
    pattern = re.compile(r'\{([^{}]+)\}')

    for para in doc.paragraphs:
        text = para.text
        matches = pattern.findall(text)
        placeholders.update(matches)

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text = cell.text
                matches = pattern.findall(text)
                placeholders.update(matches)

    return list(placeholders)

def replace_placeholders(doc, data):
    """
    Replace all placeholders in the document with values from data dict.
    Works on paragraphs and tables, preserving formatting from the first run.
    """
    pattern = re.compile(r'\{([^{}]+)\}')

    def replace_in_text(text):
        def repl(match):
            key = match.group(1)
            return data.get(key, match.group(0))
        return pattern.sub(repl, text)

    # Process paragraphs
    for para in doc.paragraphs:
        text = para.text
        if pattern.search(text):
            new_text = replace_in_text(text)
            # Preserve formatting from the first run (if any)
            if para.runs:
                first_run = para.runs[0]
                font = first_run.font
                bold = font.bold
                italic = font.italic
                underline = font.underline
                color = font.color.rgb if font.color else None
                size = font.size
                name = font.name
                # Clear all runs and add new text
                para.clear()
                run = para.add_run(new_text)
                # Restore formatting
                run.font.bold = bold
                run.font.italic = italic
                run.font.underline = underline
                if color:
                    run.font.color.rgb = color
                run.font.size = size
                run.font.name = name
            else:
                # No runs → create one with default style
                para.clear()
                run = para.add_run(new_text)
                run.font.name = "Mangal"
                run.font.size = Pt(14)

    # Process tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for para in cell.paragraphs:
                    text = para.text
                    if pattern.search(text):
                        new_text = replace_in_text(text)
                        if para.runs:
                            first_run = para.runs[0]
                            font = first_run.font
                            bold = font.bold
                            italic = font.italic
                            underline = font.underline
                            color = font.color.rgb if font.color else None
                            size = font.size
                            name = font.name
                            para.clear()
                            run = para.add_run(new_text)
                            run.font.bold = bold
                            run.font.italic = italic
                            run.font.underline = underline
                            if color:
                                run.font.color.rgb = color
                            run.font.size = size
                            run.font.name = name
                        else:
                            para.clear()
                            run = para.add_run(new_text)
                            run.font.name = "Mangal"
                            run.font.size = Pt(14)

    return doc

def create_filled_document(template_path, data, output_path):
    """
    Load template, replace placeholders, save to output_path.
    """
    doc = Document(template_path)
    doc = replace_placeholders(doc, data)
    doc.save(output_path)
    return output_path