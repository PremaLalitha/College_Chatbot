from flask import Flask, render_template, request, jsonify
import os
import re
import difflib

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
try:
    from langchain_groq import ChatGroq
except ImportError:
    ChatGroq = None


# ============================================================
# NLP UNDERSTANDING & PREPROCESSING MODULE
# ============================================================

import json
from datetime import datetime

SYNONYM_MAP = {
    r"\bcse\b": "computer science and engineering",
    r"\bece\b": "electronics and communication engineering",
    r"\beee\b": "electrical and electronics engineering",
    r"\bmech\b": "mechanical engineering",
    r"\bmechanical\b": "mechanical engineering",
    r"\bit\b": "information technology",
    r"\bai\b": "artificial intelligence and data science",
    r"\baids\b": "artificial intelligence and data science",
    r"\bai\s*&\s*ds\b": "artificial intelligence and data science",
    r"\bbtech\b": "b.tech",
    r"\bbe\b": "b.e",
    r"\bme\b": "m.e",
    r"\bmtech\b": "m.tech",
    r"\bundergrad\b": "undergraduate",
    r"\bunder graduate\b": "undergraduate",
    r"\bpostgrad\b": "postgraduate",
    r"\bpost graduate\b": "postgraduate",
    r"\bdept head\b": "hod",
    r"\bdepartment head\b": "hod",
    r"\bhead of dept\b": "hod",
    r"\bhead of department\b": "hod",
    r"\bplacetent\b": "placement",
    r"\badmision\b": "admission",
    r"\bschalthip\b": "scholarship",
    r"\bscholarships\b": "scholarship",
    r"\bhostel food\b": "hostel food",
    r"\bmess food\b": "mess food",
    r"\bbus facility\b": "bus transport",
    r"\btnea\b": "tamil nadu engineering admissions tnea",
    r"\bnaac\b": "naac accreditation",
    r"\bnba\b": "nba accreditation",
    r"\bnirf\b": "nirf ranking",
    r"\bcanteen\b": "cafeteria",
}

KEYWORD_VOCABULARY = [
    "placement", "admission", "courses", "hostel", "transport",
    "scholarship", "library", "department", "academics", "research",
    "facilities", "safety", "contact", "principal", "convener",
    "coordinator", "curriculum", "syllabus", "regulations", "eligibility",
    "accreditation", "ranking", "tnea", "cutoff", "tuition", "cafeteria"
]

def preprocess_nlp_query(question):
    """
    Applies NLP normalization, acronym expansion, and fuzzy spelling correction
    to user queries before RAG retrieval.
    """
    q = question.lower().strip()

    # 1. Expand acronyms and normalize domain synonyms
    for pattern, replacement in SYNONYM_MAP.items():
        q = re.sub(pattern, replacement, q)

    # 2. Fuzzy spelling correction for typos on long words
    words = q.split()
    corrected_words = []
    for word in words:
        clean_w = re.sub(r"[^\w]", "", word)
        if len(clean_w) >= 5 and clean_w not in KEYWORD_VOCABULARY:
            matches = difflib.get_close_matches(clean_w, KEYWORD_VOCABULARY, n=1, cutoff=0.8)
            if matches:
                corrected_words.append(matches[0])
            else:
                corrected_words.append(word)
        else:
            corrected_words.append(word)

    return " ".join(corrected_words)


# ============================================================
# LOGGING UTILITY
# ============================================================

def log_chat_interaction(user_data, question, answer):
    """Logs user query, response, and metadata to JSONL file."""
    try:
        data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        os.makedirs(data_dir, exist_ok=True)
        log_file = os.path.join(data_dir, "chat_logs.jsonl")

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_name": user_data.get("user_name", "Anonymous"),
            "user_location": user_data.get("user_location", "Unknown"),
            "user_source": user_data.get("user_source", "Unknown"),
            "question": question,
            "answer": answer
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")
    except Exception as err:
        print("Logging error:", err)


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# PATH
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

VECTOR_DB_PATH = os.path.join(
    BASE_DIR,
    "chroma_db"
)


# ============================================================
# MODELS
# ============================================================

EMBEDDING_MODEL = (
    "sentence-transformers/"
    "all-MiniLM-L6-v2"
)

OLLAMA_MODEL = "llama3.2:3b"


# ============================================================
# NEC CONTACT & FALLBACK CONSTANTS
# ============================================================

NEC_CONTACT = """Please contact National Engineering College for details:

Mob : 93859 76674, 93859 76684
Email: principal@nec.edu.in"""

NOT_IN_DB_FALLBACK = "This question is not in my NEC database. I am designed to answer questions only related to National Engineering College."

FALLBACK = NEC_CONTACT

COLLEGE_KEYWORDS = [
    "nec", "national engineering college", "college", "campus", "university", "institution",
    "admission", "admissions", "apply", "application", "eligibility", "document", "documents",
    "course", "courses", "programme", "programmes", "degree", "b.e", "b.tech", "m.e", "m.tech", "ug", "pg",
    "cse", "ece", "eee", "mechanical", "civil", "it", "ai", "aids", "data science", "science", "humanities",
    "placement", "placements", "recruiter", "recruiters", "salary", "package", "offer", "offers", "placed", "internship",
    "hostel", "hostels", "room", "rooms", "mess", "food", "breakfast", "lunch", "dinner",
    "bus", "buses", "transport", "route", "routes", "travel",
    "scholarship", "scholarships", "fee", "fees", "tuition", "cost", "stipend",
    "principal", "hod", "hods", "head", "founder", "director", "correspondent", "manager", "staff", "faculty", "teacher", "professor",
    "department", "departments", "academics", "curriculum", "syllabus", "exam", "exams", "examination", "result", "results", "regulation",
    "tnea", "cutoff", "counseling", "counselling", "library", "sports", "facility", "facilities", "canteen", "cafeteria", "computer",
    "bank", "banking", "atm", "cash",
    "anti-ragging", "ragging", "grievance", "icc", "safety", "support",
    "contact", "phone", "email", "address", "location", "kovilpatti", "thoothukudi", "tuticorin", "tirunelveli", "madurai",
    "anna university", "autonomous", "naac", "nba", "nirf", "aicte",
    "research", "patent", "patents", "publication", "publications", "club", "clubs", "ncc", "nss", "event", "events"
]

def is_greeting(question):
    q = question.lower().strip()
    clean_q = re.sub(r"[^\w\s]", "", q)
    return clean_q in ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "namaste", "greetings"]

def is_college_related_query(question):
    q = question.lower().strip()
    return any(k in q for k in COLLEGE_KEYWORDS)


# ============================================================
# LOAD EMBEDDING MODEL & CHROMA (LAZY LOADING)
# ============================================================

_embeddings = None
_vector_db = None

def get_vector_db():
    global _embeddings, _vector_db
    if _vector_db is None:
        print()
        print("Loading embedding model...")
        _embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL
        )
        print("Embedding model loaded successfully.")

        print()
        print("Loading NEC vector database...")
        if not os.path.exists(VECTOR_DB_PATH):
            raise FileNotFoundError(
                "Chroma database not found.\n"
                "Run:\n"
                "python src/load_data.py\n"
                "python src/create_embeddings.py"
            )

        _vector_db = Chroma(
            persist_directory=VECTOR_DB_PATH,
            embedding_function=_embeddings,
            collection_name="nec_knowledge"
        )
        print("Vector database loaded successfully.")
    return _vector_db


# ============================================================
# LOAD LLM (Groq for Cloud / Render or Ollama for Local)
# ============================================================

print()
groq_key = os.getenv("GROQ_API_KEY")
if groq_key and ChatGroq:
    print("Loading Cloud LLM (Groq)...")
    llm = ChatGroq(
        model_name="llama-3.3-70b-versatile",
        groq_api_key=groq_key,
        temperature=0
    )
    print("Groq LLM loaded successfully.")
else:
    print("Loading Ollama...")
    llm = ChatOllama(
        model=OLLAMA_MODEL,
        temperature=0
    )
    print("Ollama loaded successfully.")


# ============================================================
# QUESTION CATEGORY
# ============================================================

def detect_question_category(question):

    q = question.lower().strip()


    # --------------------------------------------------------
    # COURSES
    # --------------------------------------------------------

    if any(word in q for word in [
        "course",
        "courses",
        "programme",
        "programmes",
        "degree",
        "b.e",
        "b.tech",
        "m.e",
        "m.tech",
        "after 12th",
        "after school",
        "undergraduate",
        "postgraduate",
        "ug",
        "pg"
    ]):

        return "courses"


    # --------------------------------------------------------
    # PLACEMENT
    # --------------------------------------------------------

    if any(word in q for word in [
        "placement",
        "package",
        "salary",
        "recruiter",
        "recruit",
        "placed",
        "placement statistics",
        "placement convener",
        "placement coordinator",
        "placement centre",
        "placement center",
        "internship"
    ]):

        return "placement"


    # --------------------------------------------------------
    # DEPARTMENT
    # --------------------------------------------------------

    if any(word in q for word in [
        "department",
        "hod",
        "head of department"
    ]):

        return "department"


    # --------------------------------------------------------
    # ACADEMICS
    # --------------------------------------------------------

    if any(word in q for word in [
        "curriculum",
        "syllabus",
        "regulation",
        "academic calendar",
        "exam",
        "examination",
        "attendance"
    ]):

        return "academics"


    # --------------------------------------------------------
    # RESEARCH
    # --------------------------------------------------------

    if any(word in q for word in [
        "research",
        "innovation",
        "patent",
        "incubator",
        "entrepreneurship"
    ]):

        return "research"


    # --------------------------------------------------------
    # STUDENT LIFE
    # --------------------------------------------------------

    if any(word in q for word in [
        "club",
        "clubs",
        "ncc",
        "nss",
        "yoga",
        "literary",
        "quiz club",
        "eco club",
        "fine arts"
    ]):

        return "student_life"


    # --------------------------------------------------------
    # FACILITIES
    # --------------------------------------------------------

    if any(word in q for word in [
        "facility",
        "facilities",
        "cafeteria",
        "health care",
        "computer centre",
        "computer center",
        "sports facility"
    ]):

        return "facilities"


    # --------------------------------------------------------
    # SAFETY
    # --------------------------------------------------------

    if any(word in q for word in [
        "ragging",
        "anti ragging",
        "safety",
        "complaint",
        "icc",
        "disciplinary"
    ]):

        return "safety"


    # --------------------------------------------------------
    # CONTACT
    # --------------------------------------------------------

    if any(word in q for word in [
        "contact",
        "phone number",
        "telephone",
        "email",
        "address",
        "website"
    ]):

        return "contact"


    # --------------------------------------------------------
    # ABOUT
    # --------------------------------------------------------

    if any(word in q for word in [
        "founder",
        "director",
        "principal",
        "correspondent",
        "established",
        "vision",
        "mission",
        "about nec"
    ]):

        return "about"


    return "general"


# ============================================================
# FIXED CONTACT QUESTIONS
# ============================================================

def is_contact_request(question):

    q = question.lower().strip()

    contact_words = [
        "contact",
        "phone number",
        "telephone number",
        "mobile number",
        "email address",
        "email id",
        "how can i contact",
        "how to contact"
    ]

    return any(
        word in q
        for word in contact_words
    )


def is_online_admission_query(question):
    q = question.lower().strip()
    online_terms = [
        "online admission", "apply online", "online application", "admission online",
        "is admission available online", "is online admission available",
        "can i apply online", "how to apply online", "online form", "apply through online",
        "admission available in online", "admission available online"
    ]
    return any(term in q for term in online_terms)

def is_fee_query(question):
    q = question.lower().strip()
    fee_terms = [
        "fee", "fees", "tuition", "cost", "cost of study",
        "hostel fee", "hostel fees", "transport fee", "transport fees",
        "bus fee", "bus fees", "mess fee", "mess fees",
        "college fee", "college fees", "fee structure", "semester fee", "annual fee"
    ]
    return any(term in q for term in fee_terms)

def is_eligibility_query(question):
    q = question.lower().strip()
    eligibility_terms = [
        "eligibility", "eligible", "qualification for admission", "qualification to join",
        "eligibility criteria", "eligibility to join", "criteria to join", "requirement to join",
        "eligibility for join", "am i eligible"
    ]
    return any(term in q for term in eligibility_terms)

def requires_contact_fallback(question):

    q = question.lower().strip()

    fallback_phrases = [

        # Online admission
        "online admission",
        "online admission process",
        "online application",
        "apply online",
        "can i apply online",
        "how to apply online",

        # Current fees
        "current tuition fee",
        "current tuition fees",
        "current college fee",
        "current college fees",
        "current fee",
        "current fees",

        # Hostel fee
        "current hostel fee",
        "current hostel fees",
        "hostel fee",

        # Transport fee
        "current transport fee",
        "current transport fees",
        "transport fee"
    ]

    return any(
        phrase in q
        for phrase in fallback_phrases
    )


# ============================================================
# EXACT IMPORTANT FACTS
# ============================================================

def get_exact_answer(question):

    q = question.lower().strip()


    # --------------------------------------------------------
    # COURSES / UG PROGRAMMES
    # --------------------------------------------------------

    if any(phrase in q for phrase in [
        "ug courses",
        "undergraduate courses",
        "ug programmes",
        "courses after 12th",
        "courses can i join after 12th",
        "b.e courses",
        "b.tech courses"
    ]):

        return (
            "### National Engineering College - Undergraduate (UG) Programmes\n\n"
            "1. **B.E. Computer Science and Engineering** (B.E. CSE)\n"
            "2. **B.E. Electronics and Communication Engineering** (B.E. ECE)\n"
            "3. **B.E. Mechanical Engineering** (B.E. Mechanical)\n"
            "4. **B.E. Electrical and Electronics Engineering** (B.E. EEE)\n"
            "5. **B.E. Civil Engineering** (B.E. Civil)\n"
            "6. **B.Tech. Information Technology** (B.Tech. IT)\n"
            "7. **B.Tech. Artificial Intelligence and Data Science** (B.Tech. AI & DS)"
        )


    # --------------------------------------------------------
    # PG PROGRAMMES
    # --------------------------------------------------------

    if any(phrase in q for phrase in [
        "pg courses",
        "postgraduate courses",
        "pg programmes",
        "m.e courses",
        "m.tech courses"
    ]):

        return (
            "### National Engineering College - Postgraduate (PG) Programmes\n\n"
            "1. **M.E. Computer Science and Engineering** (M.E. CSE)\n"
            "2. **M.E. Energy Engineering**\n"
            "3. **M.E. High Voltage Engineering**\n"
            "4. **M.E. Embedded Systems Technologies**\n"
            "5. **M.Tech. Information Technology** (Information and Cyber Warfare)"
        )


    # --------------------------------------------------------
    # OFFICIALS
    # --------------------------------------------------------

    if "principal" in q:

        return (
            "### Principal\n\n"
            "**Dr. K. Kalidasa Murugavel**\n\n"
            "National Engineering College, Kovilpatti."
        )


    if "founder" in q:

        return (
            "### Founder\n\n"
            "**Thiru. K. Ramasamy**\n\n"
            "Founder of National Engineering College (Established 1984)."
        )


    if "director" in q:

        return (
            "### Director\n\n"
            "**Dr. S. Shanmugavel**"
        )


    if "correspondent" in q:

        return (
            "### Correspondent\n\n"
            "**Thiru. K. R. Arunachalam**"
        )


    # --------------------------------------------------------
    # HEAD OF DEPARTMENTS (HODs)
    # --------------------------------------------------------

    if "hod of cse" in q or "head of cse" in q or "cse hod" in q:

        return "### Head of Department (CSE)\n\n**Dr. V. Gomathi**"


    if "hod of ece" in q or "head of ece" in q or "ece hod" in q:

        return "### Head of Department (ECE)\n\n**Dr. S. Tamilselvi**"


    if "hod of eee" in q or "head of eee" in q or "eee hod" in q:

        return "### Head of Department (EEE)\n\n**Dr. M. Willjuice Iruthayarajan**"


    if "hod of mechanical" in q or "head of mechanical" in q or "mechanical hod" in q:

        return "### Head of Department (Mechanical)\n\n**Dr. S. Iyahraja**"


    if "hod of civil" in q or "head of civil" in q or "civil hod" in q:

        return "### Head of Department (Civil)\n\n**Dr. I. Padmanaban**"


    if "hod of it" in q or "head of it" in q or "it hod" in q:

        return "### Head of Department (Information Technology)\n\n**Dr. R. Muthukkumar**"


    if "hod of ai & ds" in q or "head of ai" in q or "ai hod" in q or "aids hod" in q:

        return "### Head of Department (AI & DS)\n\n**Dr. V. Kalaivani**"


    if any(term in q for term in ["bank", "atm", "banking", "cash machine"]):

        return (
            "### Banking & ATM Facilities\n\n"
            "Yes, **National Engineering College (NEC)** provides a **Banking facility with an ATM** on campus for the convenience of students, faculty, and hostellers."
        )


    if any(phrase in q for phrase in [
        "placement training",
        "placement training does nec provide",
        "training for placement",
        "placement preparation",
        "what placement training"
    ]):

        return (
            "### Placement Training at NEC\n\n"
            "National Engineering College (NEC) provides comprehensive placement training to prepare students for campus placement drives:\n\n"
            "1. **Communication & Soft Skills Training**\n"
            "2. **Logical Reasoning & Quantitative Aptitude**\n"
            "3. **Technical & Coding Skill Enhancement**\n"
            "4. **Resume Writing & Profile Building**\n"
            "5. **Group Discussions (GD) & Confidence Building**\n"
            "6. **Mock Technical & HR Interviews**\n"
            "7. **Personality Development Workshops**\n"
            "8. **Industry Expert Interaction & Company-Specific Training**"
        )


    if "placement convener" in q or "convener of placement" in q:

        return (
            "### Placement Convener\n\n"
            "**Dr. V. Manimaran**"
        )


    if "placement coordinator" in q or "coordinator of placement" in q:

        return (
            "### Placement Coordinators\n\n"
            "1. **Dr. D. Vigneshkumar**\n"
            "2. **Mr. M. Sathiskumar**"
        )


    if "transport manager" in q:

        return (
            "### Transport Manager\n\n"
            "**V. Alagar Ramanujam**"
        )


    return None


# ============================================================
# CLEAN ANSWER
# ============================================================

def clean_answer(answer):

    if not answer:
        return answer

    answer = answer.strip()

    # Remove ANSWER prefix
    answer = re.sub(
        r"^ANSWER\s*:\s*",
        "",
        answer,
        flags=re.IGNORECASE
    )

    # Remove excessive blank lines
    answer = re.sub(
        r"\n{3,}",
        "\n\n",
        answer
    )

    # STRICT NAME & PHONE CLEANER FOR PERSONNEL & CONTACTS
    # 1. Remove dashes/colons followed by phone numbers attached to names/titles (e.g. Dr. V. Manimaran — 94432 30265 -> Dr. V. Manimaran)
    answer = re.sub(r"\s*[—–\-:]+\s*(?:\+91[\s-]*)?(?:[6-9]\d{4}\s*\d{5}|[6-9]\d{9}|04632[^\n.]*)\b", "", answer)

    # 2. Match any remaining landlines with 04632
    answer = re.sub(r"04632\s*[–—\-\d\s,ext.&]+", "", answer)

    # 3. Match extension patterns (e.g. ext. 1062 & 1025, 1062 & 1025, Placement Centre 1062 & 1025)
    answer = re.sub(r"\bext\.?\s*\d+(?:\s*&\s*\d+)?", "", answer, flags=re.IGNORECASE)
    answer = re.sub(r"\bPlacement Centre\s*[.:–—\-]*\s*\d+[\d\s&]*", "", answer, flags=re.IGNORECASE)
    answer = re.sub(r"\b\d{4}\s*&\s*\d{4}\b", "", answer)

    # 4. Match any 10-digit or 5+5 digit phone numbers that are NOT approved official contact
    def replace_num(m):
        raw = m.group(0)
        digits = re.sub(r"\D", "", raw)
        if digits in ["9385976674", "9385976684"]:
            return raw
        return ""

    answer = re.sub(r"\b[6-9]\d{4}\s*\d{5}\b", replace_num, answer)
    answer = re.sub(r"\b[6-9]\d{9}\b", replace_num, answer)

    # 5. Clean up empty bullets and trailing punctuation left after stripping numbers
    lines = answer.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped_line = re.sub(r"^\s*[*•\-]\s*[.:–—\-]*\s*$", "", line).strip()
        if stripped_line:
            cleaned_lines.append(line)
    answer = "\n".join(cleaned_lines)

    # 6. Remove any emoji characters
    answer = re.sub(r"[\U00010000-\U0010ffff\u2600-\u27ff\u2300-\u23ff]", "", answer)

    # 7. Clean up duplicate spaces and excessive newlines
    answer = re.sub(r"\s+([.,])", r"\1", answer)
    answer = re.sub(r"[ \t]+", " ", answer)
    answer = re.sub(r"\n{3,}", "\n\n", answer)

    return answer.strip()


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():

    return render_template(
        "index.html"
    )


# ============================================================
# CHAT
# ============================================================

@app.route(
    "/chat",
    methods=["POST"]
)
def chat():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    question = data.get(
        "question",
        ""
    ).strip()

    user_data = {
        "user_name": data.get("user_name", "Anonymous"),
        "user_location": data.get("user_location", "Unknown"),
        "user_source": data.get("user_source", "Unknown")
    }

    def respond(ans_text):
        log_chat_interaction(user_data, question, ans_text)
        return jsonify({"answer": ans_text})

    if not question:
        return respond("Please enter your question.")

    if is_greeting(question):
        return respond("Hello! Welcome to National Engineering College Assistant. How can I help you today with information about NEC?")

    # Apply NLP Preprocessing & Normalization
    nlp_question = preprocess_nlp_query(question)

    print()
    print(
        f"User Question: {question}"
    )
    if nlp_question != question.lower().strip():
        print(
            f"NLP Normalized Query: {nlp_question}"
        )

    # Filter out off-topic non-college questions (e.g. "did u eat", "what is 2+2")
    if not is_college_related_query(nlp_question) and not is_college_related_query(question):
        print("Non-college / off-topic question detected. Returning NOT_IN_DB_FALLBACK.")
        return respond(NOT_IN_DB_FALLBACK)

    # ========================================================
    # 1. ONLINE ADMISSION QUERY
    # ========================================================

    if is_online_admission_query(nlp_question) or is_online_admission_query(question):

        print(
            "Online admission query detected."
        )

        return respond(
            "No, online admission is not available. Please contact National Engineering College for admission details:\n\n"
            "Mob : 93859 76674, 93859 76684\n"
            "Email: principal@nec.edu.in"
        )

    # ========================================================
    # 2. FEE DETAILS QUERY
    # ========================================================

    if is_fee_query(nlp_question) or is_fee_query(question):

        print(
            "Fee details query detected."
        )

        return respond(
            "Please contact National Engineering College for fee details:\n\n"
            "Mob : 93859 76674, 93859 76684\n"
            "Email: principal@nec.edu.in"
        )

    # ========================================================
    # 3. ELIGIBILITY QUERY
    # ========================================================

    if is_eligibility_query(nlp_question) or is_eligibility_query(question):

        print(
            "Eligibility query detected."
        )

        return respond(
            "Please contact National Engineering College for eligibility details:\n\n"
            "Mob : 93859 76674, 93859 76684\n"
            "Email: principal@nec.edu.in"
        )

    # ========================================================
    # 4. GENERAL CONTACT REQUEST
    # ========================================================

    if is_contact_request(nlp_question) or is_contact_request(question):

        print(
            "Using fixed NEC contact information."
        )

        return respond(NEC_CONTACT)

    # ========================================================
    # 5. QUESTIONS THAT MUST USE CONTACT FALLBACK
    # ========================================================

    if requires_contact_fallback(nlp_question) or requires_contact_fallback(question):

        print(
            "Using NEC contact fallback."
        )

        return respond(FALLBACK)


    # ========================================================
    # 3. EXACT IMPORTANT FACTS
    # ========================================================

    exact_answer = get_exact_answer(
        nlp_question
    ) or get_exact_answer(question)


    if exact_answer:

        print(
            "Using exact NEC information."
        )

        return respond(exact_answer)


    # ========================================================
    # 4. CATEGORY
    # ========================================================

    category = (
        detect_question_category(
            nlp_question
        )
    )


    print(
        f"Detected category: {category}"
    )


    # ========================================================
    # 5. RETRIEVAL
    # ========================================================

    try:

        vdb = get_vector_db()
        # 1. Global semantic search (captures relevant chunks regardless of category tag)
        global_docs = vdb.similarity_search(nlp_question, k=6)

        # 2. Category-filtered search if category detected
        cat_docs = []
        if category != "general":
            try:
                cat_docs = vdb.similarity_search(nlp_question, k=4, filter={"category": category})
            except Exception as err:
                print("Category search error:", err)

        # 3. Deduplicate preserving order
        seen_texts = set()
        documents = []
        for doc in global_docs + cat_docs:
            if doc.page_content not in seen_texts:
                seen_texts.add(doc.page_content)
                documents.append(doc)


    except Exception as error:

        print(
            "Retrieval error:",
            error
        )

        return respond(FALLBACK)


    if not documents:

        return respond(FALLBACK)


    # ========================================================
    # 6. BUILD CONTEXT
    # ========================================================

    context_parts = []


    for document in documents:

        section = (
            document.metadata.get(
                "section",
                "NEC"
            )
        )

        context_parts.append(
            f"SECTION: {section}\n\n"
            f"{document.page_content}"
        )


    context = "\n\n".join(
        context_parts
    )


    # ========================================================
    # 7. PROMPT
    # ========================================================

    prompt = f"""
You are the official National Engineering College (NEC) chatbot.

Answer ONLY using the retrieved NEC information provided below.
The retrieved information is your SINGLE SOURCE OF TRUTH.

==================================================
ABSOLUTE SOURCE & NO HALLUCINATION RULES
==================================================
1. Answer ONLY from the retrieved content of the NEC knowledge base.
2. DO NOT use outside knowledge, personal assumptions, or guessing.
3. NEVER invent or infer fees, dates, numbers, phone numbers, or email addresses.
4. Do NOT calculate, estimate, assume, or predict information unless explicitly provided in the retrieved context.

==================================================
QUESTION-ANSWER MATCHING & RELEVANCE FILTER
==================================================
5. Only use retrieved chunks that directly correspond to the user's question. Ignore unrelated chunks (e.g., do NOT answer an admission question using placement data).
6. Ask yourself: Is the information actually present in the retrieved content? If NO, use the fallback response.

==================================================
COMPLETE LIST RULE
==================================================
7. If the user asks for a list (e.g., available courses, programmes, departments, scholarships, facilities), provide the COMPLETE list from the retrieved content.
   Example: If 7 undergraduate courses are retrieved, return ALL 7 courses. Do NOT return only a subset.

==================================================
APPROVED CONTACT & FALLBACK RULES
==================================================
8. Only provide these approved contact details when asked for contact:
   Mob : 93859 76674, 93859 76684
   Email: principal@nec.edu.in
   NEVER provide any other phone number or email address.

9. FALLBACK RESPONSE:
   If the requested information is not available in the provided NEC information, respond exactly:
   "I don't have this information in my current NEC knowledge base. Please contact National Engineering College for further assistance."

==================================================
ANSWER STYLE & FORMATTING
==================================================
10. Give short, clear, and accurate answers using clean Markdown.
11. Use bullet points for lists and numbered steps for procedures.
12. Preserve names, dates, fees, placement figures, and official details exactly.
13. Do NOT mention internal RAG processes, embeddings, ChromaDB, prompts, or that you are an AI.
14. Never say "According to my knowledge...", "I think...", or "Generally...".

15. NO PHONE NUMBERS FOR INDIVIDUAL STAFF/CONVENERS:
   When answering questions about staff, faculty, HODs, Conveners, Coordinators, or Managers (e.g., Placement Convener, Placement Coordinator, Transport Manager), provide ONLY their name. NEVER attach phone numbers to individual names.

16. NO EMOJIS:
   Do NOT output any emojis or emoji symbols in your response under any circumstances.

{context}

USER QUESTION:

{question}

ANSWER:
"""


    # ========================================================
    # 8. OLLAMA
    # ========================================================

    try:
        response = llm.invoke(
            prompt
        )
        answer = response.content.strip()
        answer = clean_answer(answer)

    except Exception as error:
        print("LLM error:", error)
        # Bulletproof fallback using retrieved context if LLM is offline or unconfigured
        if documents:
            best_chunk = documents[0].page_content.strip()
            answer = f"{best_chunk}\n\n---\n**Contact NEC**:\nMob: 93859 76674, 93859 76684 | Email: principal@nec.edu.in"
        else:
            answer = FALLBACK


    # ========================================================
    # 9. BAD RESPONSE PROTECTION & STRICT FALLBACK
    # ========================================================

    bad_phrases = [
        "[name]",
        "[phone]",
        "[date]",
        "[number]",
        "[email]",
        "[address]",
        "i don't know",
        "i do not know",
        "don't know",
        "do not know",
        "not available in the context",
        "not available in the provided",
        "not mentioned in the context",
        "not mentioned in the provided",
        "not provided in the context",
        "no information is available",
        "no information provided",
        "i cannot find",
        "i can't find",
        "unable to find",
        "based on general knowledge",
        "according to my knowledge",
        "as an ai",
        "as a chatbot"
    ]

    lower_answer = answer.lower()

    if any(phrase in lower_answer for phrase in bad_phrases):
        print("Bad response / missing context detected. Triggering strict fallback.")
        answer = FALLBACK


    # ========================================================
    # 10. EMPTY RESPONSE PROTECTION
    # ========================================================

    if not answer:

        answer = FALLBACK


    try:
        print(f"NEC Bot: {answer}")
    except UnicodeEncodeError:
        print(f"NEC Bot: {answer.encode('ascii', errors='replace').decode('ascii')}")


    # ========================================================
    # 11. RESPONSE
    # ========================================================

    return respond(answer)


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print()
    print(
        "=========================================="
    )

    print(
        "     NATIONAL ENGINEERING COLLEGE"
    )

    print(
        "             NEC CHATBOT"
    )

    print(
        "=========================================="
    )

    print()

    print(
        "Open: http://127.0.0.1:5000"
    )

    print()


    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
        use_reloader=False
    )