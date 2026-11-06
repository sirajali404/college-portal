import streamlit as st
import sqlite3
import os
import uuid
import hashlib
from datetime import date, datetime
from pathlib import Path

# =========================================================
# COLLEGE WEBSITE - BEGINNER_CODER
# Local/demo starter project. Read the security notes first.
# =========================================================

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "college.db"
UPLOAD_DIR = APP_DIR / "private_uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Set this environment variable before deployment.
# Do not use the demo fallback password on a public website.
ADMIN_PASSWORD = os.environ.get("COLLEGE_ADMIN_PASSWORD", "ChangeMe123!")

st.set_page_config(
    page_title="Abdulla Hospital | Admissions Portal",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ------------------------- THEME -------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
    --bg: #050914;
    --panel: #0b1424;
    --panel2: #101d32;
    --blue: #19a7ff;
    --cyan: #35e0ff;
    --text: #eaf4ff;
    --muted: #91a8c2;
}
.stApp {
    background:
      radial-gradient(circle at 12% 5%, rgba(0,145,255,.14), transparent 28%),
      radial-gradient(circle at 90% 18%, rgba(0,225,255,.08), transparent 25%),
      var(--bg);
    color: var(--text);
    font-family: 'Inter', sans-serif;
}
[data-testid="stHeader"] { background: rgba(5,9,20,.75); }
.block-container { padding-top: 1.7rem; padding-bottom: 3rem; max-width: 1250px; }
h1, h2, h3 { color: #f3f9ff !important; letter-spacing: -.4px; }
p, label, li { color: #d8e8f8; }
.small-muted { color: var(--muted); font-size: .9rem; }
.hero {
    padding: 34px 32px; border-radius: 22px;
    background: linear-gradient(120deg, rgba(12,32,58,.98), rgba(5,15,31,.96));
    border: 1px solid rgba(25,167,255,.45);
    box-shadow: 0 0 30px rgba(0,145,255,.12), inset 0 0 25px rgba(0,145,255,.04);
}
.hero-tag {
    color: var(--cyan); font-weight: 800; letter-spacing: 2px;
    font-size: .75rem; text-transform: uppercase;
}
.hero-title { font-size: clamp(2rem, 5vw, 3.5rem); font-weight: 800; line-height: 1.08; margin: 10px 0; }
.hero-desc { color: #a9c2dc; max-width: 720px; }
.glow-card {
    background: linear-gradient(145deg, #0d1b30, #081222);
    border: 1px solid rgba(25,167,255,.28);
    border-radius: 16px; padding: 18px 20px;
    box-shadow: 0 8px 28px rgba(0,0,0,.18);
}
.card-label { color: #8da9c6; font-size: .78rem; text-transform: uppercase; letter-spacing: 1px; }
.card-value { color: #eaf7ff; font-size: 1.55rem; font-weight: 800; margin-top: 5px; }
div.stButton > button, div.stFormSubmitButton > button {
    background: linear-gradient(90deg, #087bd1, #08a9d8);
    color: white; border: 1px solid #35caff; border-radius: 10px;
    font-weight: 700; min-height: 42px;
    box-shadow: 0 0 16px rgba(0,153,255,.17);
}
div.stButton > button:hover, div.stFormSubmitButton > button:hover {
    border-color: #8ceaff; color: white; transform: translateY(-1px);
    box-shadow: 0 0 22px rgba(0,180,255,.28);
}
input, textarea {
    background: #0b1728 !important; color: #eaf4ff !important;
}
[data-baseweb="select"] > div { background: #0b1728; }
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #081426, #050b16);
    border-right: 1px solid rgba(25,167,255,.25);
}
[data-testid="stSidebar"] * { color: #dceeff; }
hr { border-color: rgba(25,167,255,.22); }
div[data-testid="stMetric"] {
    background: #0b1728; border: 1px solid rgba(25,167,255,.25);
    padding: 14px; border-radius: 14px;
}
footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ------------------------- DATABASE -------------------------
def connect_db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    with connect_db() as con:
        con.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_no TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            guardian_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT,
            program TEXT NOT NULL,
            previous_education TEXT NOT NULL,
            marks TEXT,
            address TEXT,
            submitted_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Submitted'
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS fee_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            challan_no TEXT UNIQUE NOT NULL,
            application_no TEXT NOT NULL,
            student_name TEXT NOT NULL,
            program TEXT NOT NULL,
            amount INTEGER NOT NULL,
            payment_reference TEXT,
            proof_filename TEXT,
            submitted_at TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Proof Submitted'
        )
        """)
        con.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """)
        count = con.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
        if count == 0:
            con.execute(
                "INSERT INTO notices(title, body, created_at) VALUES (?, ?, ?)",
                ("Admissions Open", "Applications are now being accepted. Please check eligibility and deadlines.",
                 datetime.now().strftime("%Y-%m-%d %H:%M"))
            )

init_db()

def save_uploaded_file(uploaded, prefix):
    if uploaded is None:
        return ""
    suffix = Path(uploaded.name).suffix.lower()
    allowed = {".png", ".jpg", ".jpeg", ".pdf"}
    if suffix not in allowed:
        raise ValueError("Only PDF, PNG, JPG and JPEG files are allowed.")
    if uploaded.size > 5 * 1024 * 1024:
        raise ValueError("File must be 5 MB or smaller.")
    safe_name = f"{prefix}_{uuid.uuid4().hex}{suffix}"
    target = UPLOAD_DIR / safe_name
    target.write_bytes(uploaded.getvalue())
    return safe_name

def make_application_no():
    return "AHC-" + uuid.uuid4().hex[:8].upper()

def make_challan_no():
    return "FEE-" + uuid.uuid4().hex[:8].upper()

def get_fee(program):
    fees = {
        "FSc Pre-Medical": 18000,
        "FSc Pre-Engineering": 18000,
        "ICS": 16000,
        "FA": 14000,
        "ADP / Associate Degree": 25000
    }
    return fees.get(program, 15000)

def card(label, value, note=""):
    st.markdown(
        f'<div class="glow-card"><div class="card-label">{label}</div>'
        f'<div class="card-value">{value}</div><div class="small-muted">{note}</div></div>',
        unsafe_allow_html=True
    )

# ------------------------- SIDEBAR -------------------------
with st.sidebar:
    st.markdown("## 🎓 Abdullah Hospital")
    st.caption("STUDENT & ADMISSIONS PORTAL")
    page = st.radio(
        "NAVIGATION",
        ["🏠Home", "About College", "Programs", "Admissions", "Fee Submission",
         "Notices", "Contact", "Admin Panel"],
        label_visibility="visible"
    )
    st.markdown("---")
    st.caption("© 2026 Abdullah Hospital")
    st.caption("Powered by Beginner_Coder")

# ------------------------- HOME -------------------------
if page == "🏠Home":
    st.markdown("""
    <div class="hero">
      <div class="hero-tag">LEARN • BUILD • LEAD</div>
      <div class="hero-title">Your Future Starts Here.</div>
      <div class="hero-desc">Welcome to Abdullah Hospital. Explore academic programs,
      apply for admission and stay updated with campus announcements.</div>
    </div>
    """, unsafe_allow_html=True)
    st.write("")
    c1, c2, c3 = st.columns(3)
    with c1: card("Academic Programs", "05", "Replace with actual count")
    with c2: card("Admissions", "OPEN", "Update according to official schedule")
    with c3: card("Student Support", "24/7", "Website access; office hours may differ")
    st.write("")
    st.subheader("Latest Notices")
    with connect_db() as con:
        notices = con.execute(
            "SELECT title, body, created_at FROM notices ORDER BY id DESC LIMIT 3"
        ).fetchall()
    if notices:
        for title, body, created in notices:
            with st.container(border=True):
                st.markdown(f"**{title}**")
                st.write(body)
                st.caption(created)
    else:
        st.info("No notices published yet.")
    st.info("Use the sidebar to explore programs, submit an admission application or view fee instructions.")

# ------------------------- ABOUT -------------------------
elif page == "About College":
    st.title("About Abdullah Hospital")
    st.markdown('<div class="hero"><div class="hero-tag">OUR INSTITUTION</div>'
                '<div class="hero-title">Knowledge. Skills. Future.</div>'
                '<div class="hero-desc">Add the college-approved introduction, history, mission and vision here.</div></div>',
                unsafe_allow_html=True)
    st.subheader("Our Mission")
    st.write("To provide quality education, practical skills and a supportive learning environment.")
    st.subheader("Our Vision")
    st.write("To help students become capable, responsible and lifelong learners.")
    st.warning("Replace this sample text with verified information from the actual college.")

# ------------------------- PROGRAMS -------------------------
elif page == "Programs":
    st.title("Academic Programs")
    programs = {
        "FSc Pre-Medical": ("2 Years", "Biology, Chemistry and Physics", "Sample eligibility: Matric Science."),
        "FSc Pre-Engineering": ("2 Years", "Mathematics, Chemistry and Physics", "Sample eligibility: Matric Science."),
        "ICS": ("2 Years", "Computer Science, Mathematics and relevant subjects", "Sample eligibility: As per college policy."),
        "FA": ("2 Years", "Humanities and approved elective subjects", "Sample eligibility: As per college policy."),
        "ADP / Associate Degree": ("2 Years", "Subjects depend on approved department", "Sample eligibility: Intermediate or equivalent.")
    }
    for name, info in programs.items():
        with st.container(border=True):
            st.subheader(name)
            a, b, c = st.columns(3)
            a.write(f"**Duration**\n{info[0]}")
            b.write(f"**Subjects**\n{info[1]}")
            c.write(f"**Eligibility**\n{info[2]}")
    st.caption("All program names, durations and eligibility shown here are examples. Confirm with the college.")

# ------------------------- ADMISSIONS -------------------------
elif page == "Admissions":
    st.title("Online Admission Application")
    st.write("Fill in the form carefully. Fields marked * are required.")
    with st.form("admission_form", clear_on_submit=True):
        full_name = st.text_input("Applicant full name *")
        guardian = st.text_input("Father / Guardian name *")
        phone = st.text_input("Contact number *")
        email = st.text_input("Email (optional)")
        program = st.selectbox("Select program *", [
            "FSc Pre-Medical", "FSc Pre-Engineering", "ICS", "FA", "ADP / Associate Degree"
        ])
        education = st.text_input("Previous qualification / school *")
        marks = st.text_input("Marks / grade (optional)")
        address = st.text_area("Postal address")
        photo = st.file_uploader("Photo or supporting document (PDF/JPG/PNG, max 5 MB)",
                                 type=["pdf", "png", "jpg", "jpeg"])
        agree = st.checkbox("I confirm that the information provided is correct.")
        submitted = st.form_submit_button("SUBMIT APPLICATION", use_container_width=True)
    if submitted:
        if not full_name.strip() or not guardian.strip() or not phone.strip() or not education.strip():
            st.error("Please complete all required fields.")
        elif not agree:
            st.error("Please confirm the information before submitting.")
        else:
            try:
                filename = save_uploaded_file(photo, "application") if photo else ""
                app_no = make_application_no()
                with connect_db() as con:
                    con.execute("""
                    INSERT INTO applications
                    (application_no, full_name, guardian_name, phone, email, program,
                     previous_education, marks, address, submitted_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (app_no, full_name.strip(), guardian.strip(), phone.strip(),
                          email.strip(), program, education.strip(), marks.strip(),
                          address.strip(), datetime.now().strftime("%Y-%m-%d %H:%M"),
                          "Submitted"))
                st.success("Application submitted successfully.")
                st.code(app_no)
                st.info("Save your Application Number. You will need it for fee submission and status tracking.")
            except Exception as exc:
                st.error(f"Could not submit application: {exc}")

# ------------------------- FEE SUBMISSION -------------------------
elif page == "Fee Submission":
    st.title("Fee Challan & Payment Proof")
    st.warning("DEMO WORKFLOW: This page does not transfer money or confirm a bank payment.")
    st.write("First select your program to view the sample fee amount.")
    program = st.selectbox("Program", [
        "FSc Pre-Medical", "FSc Pre-Engineering", "ICS", "FA", "ADP / Associate Degree"
    ])
    amount = get_fee(program)
    card("Sample payable amount", f"PKR {amount:,}", "Replace with official college-approved fee.")
    st.subheader("Submit your payment reference")
    with st.form("fee_form", clear_on_submit=True):
        app_no = st.text_input("Application Number *")
        student_name = st.text_input("Applicant / Student name *")
        reference = st.text_input("Bank deposit / transaction reference *")
        proof = st.file_uploader("Upload bank receipt (PDF/JPG/PNG, max 5 MB)",
                                 type=["pdf", "png", "jpg", "jpeg"])
        confirmed = st.checkbox("I confirm that this payment information is accurate.")
        send = st.form_submit_button("SUBMIT PAYMENT PROOF", use_container_width=True)
    if send:
        if not app_no.strip() or not student_name.strip() or not reference.strip() or proof is None:
            st.error("Please complete all fields and upload the receipt.")
        elif not confirmed:
            st.error("Please confirm the information.")
        else:
            try:
                with connect_db() as con:
                    app = con.execute(
                        "SELECT program FROM applications WHERE application_no = ?",
                        (app_no.strip(),)
                    ).fetchone()
                if not app:
                    st.error("Application number not found. Submit an admission form first.")
                else:
                    filename = save_uploaded_file(proof, "fee")
                    challan = make_challan_no()
                    with connect_db() as con:
                        con.execute("""
                        INSERT INTO fee_records
                        (challan_no, application_no, student_name, program, amount,
                         payment_reference, proof_filename, submitted_at, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (challan, app_no.strip(), student_name.strip(), app[0], amount,
                              reference.strip(), filename,
                              datetime.now().strftime("%Y-%m-%d %H:%M"),
                              "Proof Submitted"))
                    st.success("Payment proof submitted. It is NOT marked as paid until accounts staff verifies it.")
                    st.code(challan)
            except Exception as exc:
                st.error(f"Could not submit payment proof: {exc}")

# ------------------------- NOTICES -------------------------
elif page == "Notices":
    st.title("News & Notices")
    with connect_db() as con:
        notices = con.execute(
            "SELECT title, body, created_at FROM notices ORDER BY id DESC"
        ).fetchall()
    if notices:
        for title, body, created in notices:
            with st.container(border=True):
                st.subheader(title)
                st.write(body)
                st.caption(created)
    else:
        st.info("No notices available.")

# ------------------------- CONTACT -------------------------
elif page == "Contact":
    st.title("Contact the College")
    a, b = st.columns(2)
    with a:
        st.markdown("### Admissions Office")
        st.write("Phone: +92-XXX-XXXXXXX")
        st.write("Email: admissions@example.edu")
    with b:
        st.markdown("### Campus Address")
        st.write("Add the verified college address here.")
        st.write("Office hours: Add official timings.")
    st.caption("Replace all sample contact details before publishing.")

# ------------------------- ADMIN -------------------------
elif page == "Admin Panel":
    st.title("College Administration")
    if not st.session_state.get("admin_logged_in", False):
        st.warning("Authorized staff only.")
        with st.form("admin_login"):
            password = st.text_input("Admin password", type="password")
            login = st.form_submit_button("LOGIN", use_container_width=True)
        if login:
            if hashlib.sha256(password.encode()).hexdigest() == hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest():
                st.session_state.admin_logged_in = True
                st.rerun()
            else:
                st.error("Incorrect password.")
    else:
        if st.button("LOG OUT"):
            st.session_state.admin_logged_in = False
            st.rerun()

        with connect_db() as con:
            total_apps = con.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
            total_fees = con.execute("SELECT COUNT(*) FROM fee_records").fetchone()[0]
            pending = con.execute(
                "SELECT COUNT(*) FROM fee_records WHERE status != 'Paid / Verified'"
            ).fetchone()[0]
        m1, m2, m3 = st.columns(3)
        m1.metric("Applications", total_apps)
        m2.metric("Fee submissions", total_fees)
        m3.metric("Unverified payments", pending)

        st.subheader("Admission Applications")
        with connect_db() as con:
            rows = con.execute("""
                SELECT application_no, full_name, phone, program, submitted_at, status
                FROM applications ORDER BY id DESC
            """).fetchall()
        if rows:
            st.dataframe(
                [{"Application":r[0], "Name":r[1], "Phone":r[2], "Program":r[3],
                  "Submitted":r[4], "Status":r[5]} for r in rows],
                use_container_width=True
            )
            chosen_app = st.selectbox("Select application to update", [r[0] for r in rows])
            new_status = st.selectbox("New admission status",
                ["Submitted", "Under Review", "Missing Documents", "Accepted", "Rejected", "Waitlisted"])
            if st.button("UPDATE ADMISSION STATUS"):
                with connect_db() as con:
                    con.execute("UPDATE applications SET status=? WHERE application_no=?",
                                (new_status, chosen_app))
                st.success("Admission status updated.")
                st.rerun()
        else:
            st.info("No applications yet.")

        st.divider()
        st.subheader("Fee Proof Verification")
        with connect_db() as con:
            fees = con.execute("""
                SELECT challan_no, application_no, student_name, program, amount,
                       payment_reference, proof_filename, status
                FROM fee_records ORDER BY id DESC
            """).fetchall()
        if fees:
            st.dataframe(
                [{"Challan":r[0], "Application":r[1], "Student":r[2], "Program":r[3],
                  "Amount PKR":r[4], "Reference":r[5], "Proof file":r[6], "Status":r[7]}
                 for r in fees],
                use_container_width=True
            )
            chosen_fee = st.selectbox("Select challan to verify", [r[0] for r in fees])
            fee_status = st.selectbox("Payment decision", ["Proof Submitted", "Under Verification",
                                                           "Paid / Verified", "Rejected"])
            if st.button("UPDATE PAYMENT STATUS"):
                with connect_db() as con:
                    con.execute("UPDATE fee_records SET status=? WHERE challan_no=?",
                                (fee_status, chosen_fee))
                st.success("Payment status updated.")
                st.rerun()
        else:
            st.info("No fee proofs submitted.")

        st.divider()
        st.subheader("Publish a Notice")
        with st.form("notice_form", clear_on_submit=True):
            notice_title = st.text_input("Notice title")
            notice_body = st.text_area("Notice details")
            publish = st.form_submit_button("PUBLISH NOTICE")
        if publish:
            if notice_title.strip() and notice_body.strip():
                with connect_db() as con:
                    con.execute("INSERT INTO notices(title, body, created_at) VALUES (?, ?, ?)",
                                (notice_title.strip(), notice_body.strip(),
                                 datetime.now().strftime("%Y-%m-%d %H:%M")))
                st.success("Notice published.")
                st.rerun()
            else:
                st.error("Enter both title and details.")

st.markdown("---")
st.markdown(
    '<div style="text-align:center;color:#7892ad;font-size:12px;">'
    'Abdullah • Designed with Streamlit • <b>Beginner_Coder</b></div>',
    unsafe_allow_html=True
)
