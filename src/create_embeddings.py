import os
import re
import shutil

from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


# ============================================================
# NEC CHATBOT - CREATE EMBEDDINGS
# ============================================================

print()
print("==============================================")
print("       NEC EMBEDDING CREATION")
print("==============================================")
print()


# ============================================================
# PATHS
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)


TEXT_FILE = os.path.join(
    BASE_DIR,
    "data",
    "nec_knowledge.txt"
)


VECTOR_DB_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)


# ============================================================
# EMBEDDING MODEL
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/all-MiniLM-L6-v2"
)


# ============================================================
# CHECK TEXT FILE
# ============================================================

if not os.path.exists(TEXT_FILE):

    raise FileNotFoundError(
        f"""
Knowledge file not found:

{TEXT_FILE}

Run this first:

python src/load_data.py
"""
    )


# ============================================================
# READ KNOWLEDGE BASE
# ============================================================

print("Reading NEC knowledge base...")

with open(
    TEXT_FILE,
    "r",
    encoding="utf-8"
) as file:

    text = file.read()


print(
    f"Characters loaded: {len(text)}"
)


# ============================================================
# SECTION SPLITTING
# ============================================================

KNOWN_HEADERS = [
    "About NEC", "History", "Founder", "Management", "Vision", "Mission", "Location",
    "Admission", "UG Admission", "PG Admission", "Eligibility", "Documents", "TNEA",
    "Admission Procedure", "Admission Contact", "Fee Structure", "Tuition Fee", "Hostel Fee",
    "Academics", "Courses", "Undergraduate Courses", "Postgraduate Courses", "Curriculum",
    "Regulations", "Academic Calendar", "Examinations", "Results", "Board of Studies",
    "PEO / PO / PSO", "Departments", "CSE", "ECE", "EEE", "Mechanical", "Civil", "IT",
    "AI & DS", "Science & Humanities", "Campus Facilities", "Hostel", "Transport", "Bus Routes",
    "Library", "Web OPAC", "Sports", "Health Care", "Cafeteria", "Computer Centre",
    "E-Learning", "Placement", "Placement Training", "Placement Statistics", "Companies",
    "Highest Salary", "Average Salary", "Placement Contact", "Research", "Sponsored Research",
    "Patents", "Publications", "Consultancy", "Research Centres", "MoUs", "Student Life",
    "Clubs", "NCC", "NSS", "Student Achievements", "Events", "Student Support", "Anti-Ragging",
    "Grievance", "ICC", "SC/ST", "OBC", "Minority Cell", "Gender Equity", "POSH",
    "Anti-Drug", "Student Counsellor", "Accreditation & Ranking", "NIRF", "NAAC", "NBA",
    "AICTE", "Mandatory Disclosure", "Alumni", "Online Services", "News & Events", "Contact",
    "STRICT FALLBACK", "OFFICIAL SOURCE INDEX"
]

lines = text.splitlines()
parsed_sections = []
current_title = "General"
current_lines = []

for line in lines:
    clean_line = line.strip()
    if not clean_line:
        continue

    is_header = (clean_line in KNOWN_HEADERS) or bool(re.match(r"^\d+[A-Z]?[\.\)]\s+", clean_line))

    if is_header:
        if current_lines:
            sec_body = "\n".join(current_lines).strip()
            if len(sec_body) >= 20:
                parsed_sections.append((current_title, sec_body))
        current_title = clean_line
        current_lines = [clean_line]
    else:
        current_lines.append(clean_line)

if current_lines:
    sec_body = "\n".join(current_lines).strip()
    if len(sec_body) >= 20:
        parsed_sections.append((current_title, sec_body))

print(f"Sections identified: {len(parsed_sections)}")


# ============================================================
# CATEGORY DETECTION
# ============================================================

def detect_category(title, section_text):
    t_low = title.lower()
    val = (title + " " + section_text).lower()

    if any(k in t_low for k in ["courses", "b.e.", "b.tech", "m.e.", "m.tech", "undergraduate", "postgraduate"]):
        return "courses"
    if any(k in t_low for k in ["hostel", "gents hostel", "ladies hostel", "mess"]):
        return "hostel"
    if any(k in t_low for k in ["transport", "bus", "route"]):
        return "transport"
    if any(k in t_low for k in ["admission", "tnea", "eligibility", "documents", "counseling"]):
        return "admission"
    if any(k in t_low for k in ["placement", "recruiter", "salary", "placed", "package"]):
        return "placement"
    if any(k in t_low for k in ["scholarship", "merit", "stipend"]):
        return "scholarship"
    if any(k in t_low for k in ["library", "web opac"]):
        return "library"
    if any(k in t_low for k in ["department", "cse", "ece", "eee", "mechanical", "civil", "it", "ai & ds", "science & humanities", "hod"]):
        return "department"
    if any(k in t_low for k in ["academics", "curriculum", "syllabus", "regulations", "academic calendar", "examinations", "results"]):
        return "academics"
    if any(k in t_low for k in ["research", "patents", "publications", "consultancy", "mous"]):
        return "research"
    if any(k in t_low for k in ["student life", "clubs", "ncc", "nss", "achievements", "events"]):
        return "student_life"
    if any(k in t_low for k in ["facilities", "campus facilities", "sports", "health care", "cafeteria", "computer centre", "e-learning"]):
        return "facilities"
    if any(k in t_low for k in ["student support", "anti-ragging", "grievance", "icc", "sc/st", "obc", "posh", "minority cell"]):
        return "safety"
    if any(k in t_low for k in ["contact", "address", "phone"]):
        return "contact"
    if any(k in t_low for k in ["about", "history", "founder", "management", "vision", "mission", "location", "accreditation", "nirf", "naac", "nba"]):
        return "about"

    if "b.e. computer science" in val or "courses offered" in val or "undergraduate" in val:
        return "courses"
    if "placement" in val:
        return "placement"
    if "admission" in val:
        return "admission"
    if "hostel" in val:
        return "hostel"
    if "transport" in val or "bus" in val:
        return "transport"

    return "general"


# ============================================================
# CREATE CHUNKS
# ============================================================

documents = []
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200

for section_number, (sec_title, sec_body) in enumerate(parsed_sections, start=1):
    category = detect_category(sec_title, sec_body)

    if len(sec_body) <= CHUNK_SIZE:
        documents.append(
            Document(
                page_content=sec_body,
                metadata={
                    "source": "nec.edu.in",
                    "source_file": "NEC.docx",
                    "category": category,
                    "section": sec_title,
                    "section_number": section_number,
                    "chunk_number": 0,
                    "source_type": "official_nec_document"
                }
            )
        )
    else:
        start = 0
        chunk_number = 0
        while start < len(sec_body):
            end = start + CHUNK_SIZE
            chunk_text = sec_body[start:end].strip()
            if len(chunk_text) >= 40:
                documents.append(
                    Document(
                        page_content=chunk_text,
                        metadata={
                            "source": "nec.edu.in",
                            "source_file": "NEC.docx",
                            "category": category,
                            "section": sec_title,
                            "section_number": section_number,
                            "chunk_number": chunk_number,
                            "source_type": "official_nec_document"
                        }
                    )
                )
            chunk_number += 1
            start = end - CHUNK_OVERLAP


# ============================================================
# SHOW CHUNKS
# ============================================================

print()
print(
    f"Total chunks created: {len(documents)}"
)


# ============================================================
# REMOVE OLD CHROMA
# ============================================================

if os.path.exists(
    VECTOR_DB_PATH
):

    print()
    print(
        "Resetting old Chroma database..."
    )

    try:
        shutil.rmtree(
            VECTOR_DB_PATH
        )
    except Exception as err:
        print(f"Warning clearing directory: {err}. Re-indexing into collection...")


# ============================================================
# LOAD EMBEDDING MODEL
# ============================================================

print()
print("Loading embedding model...")

embeddings = HuggingFaceEmbeddings(

    model_name=
        EMBEDDING_MODEL

)

print(
    "Embedding model loaded successfully."
)


# ============================================================
# CREATE CHROMA
# ============================================================

print()
print(
    "Creating NEC Chroma database..."
)


vector_db = Chroma.from_documents(

    documents=documents,

    embedding=embeddings,

    persist_directory=
        VECTOR_DB_PATH,

    collection_name=
        "nec_knowledge"

)


# ============================================================
# DISPLAY CATEGORIES
# ============================================================

category_count = {}


for document in documents:

    category = document.metadata[
        "category"
    ]

    category_count[
        category
    ] = category_count.get(
        category,
        0
    ) + 1


print()
print(
    "Categories created:"
)

for category in sorted(
    category_count
):

    print(
        f"{category}: "
        f"{category_count[category]}"
    )


# ============================================================
# COMPLETED
# ============================================================

print()
print("==============================================")
print("       CHROMA DATABASE CREATED")
print("==============================================")

print()
print(
    f"Database location:\n"
    f"{VECTOR_DB_PATH}"
)

print()
print("Embedding creation completed successfully.")
print()