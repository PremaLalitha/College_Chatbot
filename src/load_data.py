from docx import Document
import os
import re


# ============================================================
# NEC CHATBOT - LOAD DATA
# ============================================================

print()
print("==============================================")
print("       NEC KNOWLEDGE BASE LOADER")
print("==============================================")
print()


# ============================================================
# PROJECT PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


# ============================================================
# INPUT DOCUMENT
# ============================================================

DOCX_PATH = os.path.join(
    BASE_DIR,
    "NEC.docx"
)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

DATA_DIR = os.path.join(
    BASE_DIR,
    "data"
)

os.makedirs(
    DATA_DIR,
    exist_ok=True
)


# ============================================================
# OUTPUT FILE
# ============================================================

OUTPUT_FILE = os.path.join(
    DATA_DIR,
    "nec_knowledge.txt"
)


# ============================================================
# CHECK DOCUMENT
# ============================================================

if not os.path.exists(DOCX_PATH):

    raise FileNotFoundError(
        f"""
NEC.docx was not found.

Expected location:
{DOCX_PATH}
"""
    )


# ============================================================
# LOAD DOCX / TEXT
# ============================================================

print("Loading NEC document...")

paragraphs = []

try:
    document = Document(
        DOCX_PATH
    )

    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            paragraphs.append(text)
except Exception:
    # Fallback to plain text reader if NEC.docx is text-encoded
    with open(DOCX_PATH, "r", encoding="utf-8", errors="ignore") as file:
        for line in file:
            text = line.strip()
            if text:
                paragraphs.append(text)


# ============================================================
# CLEAN TEXT
# ============================================================

cleaned_lines = []

for line in paragraphs:

    # Remove extra spaces
    line = re.sub(
        r"\s+",
        " ",
        line
    )

    # Normalize bullet symbol
    line = line.replace(
        "",
        "-"
    )

    # Sanitize any phone numbers to only use approved numbers
    APPROVED_CONTACT = "Mob : 93859 76674, 93859 76684"
    line = re.sub(r"04632\s*[–—\-\d\s,ext.&]+", APPROVED_CONTACT, line)

    def replace_num(m):
        raw = m.group(0)
        digits = re.sub(r"\D", "", raw)
        if digits in ["9385976674", "9385976684"]:
            return raw
        return APPROVED_CONTACT

    line = re.sub(r"\b[6-9]\d{4}\s*\d{5}\b", replace_num, line)
    line = re.sub(r"\b[6-9]\d{9}\b", replace_num, line)

    cleaned_lines.append(
        line
    )


# ============================================================
# CREATE FINAL TEXT
# ============================================================

text = "\n".join(
    cleaned_lines
)


# ============================================================
# SAVE TEXT
# ============================================================

with open(
    OUTPUT_FILE,
    "w",
    encoding="utf-8"
) as file:

    file.write(text)


# ============================================================
# INFORMATION
# ============================================================

print()
print("Document loaded successfully!")

print(
    f"Number of paragraphs: {len(paragraphs)}"
)

print(
    f"Number of characters: {len(text)}"
)

print()
print("Text file created successfully!")

print(
    f"Location:\n{OUTPUT_FILE}"
)

print()
print("First 2000 characters:")
print("----------------------------------------------")

print(
    text[:2000]
)

print("----------------------------------------------")

print()
print("==============================================")
print("        DATA LOADING COMPLETED")
print("==============================================")
print()