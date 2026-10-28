import sqlite3
from datetime import date, datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).resolve().parent
DB_PATH = APP_DIR / "recruitment_hr.db"

STATUSES = ["Applied", "Shortlisted", "Interview", "Selected", "Rejected"]
EDUCATION = ["Diploma", "Bachelor's", "Master's", "PhD", "Other"]

st.set_page_config(
    page_title="Recruitment & HR Analytics",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    .stApp {
        background: linear-gradient(135deg, #0b1020 0%, #111827 55%, #101827 100%);
        color: #eef2ff;
    }
    [data-testid="stHeader"] { background: rgba(11, 16, 32, .85); }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111827 0%, #0b1020 100%);
        border-right: 1px solid #263247;
    }
    h1, h2, h3 { color: #f8fafc !important; }
    p, label, .stMarkdown, [data-testid="stCaptionContainer"] { color: #cbd5e1; }
    div[data-testid="stMetric"] {
        background: #172033;
        border: 1px solid #29364d;
        padding: 16px 18px;
        border-radius: 14px;
    }
    div[data-testid="stMetricLabel"] { color: #a5b4fc; }
    div[data-testid="stMetricValue"] { color: #f8fafc; }
    .hero {
        padding: 28px 30px;
        border: 1px solid #2c3b56;
        border-radius: 18px;
        background: linear-gradient(120deg, #172554 0%, #1e293b 55%, #172033 100%);
        margin-bottom: 22px;
    }
    .hero h1 { margin: 0; font-size: 2.1rem; }
    .hero p { margin: 8px 0 0 0; color: #c7d2fe; }
    .panel {
        background: #151e30;
        border: 1px solid #29364d;
        border-radius: 14px;
        padding: 18px;
        margin-bottom: 12px;
    }
    .empty {
        background: #151e30;
        border: 1px dashed #475569;
        border-radius: 16px;
        padding: 28px;
        text-align: center;
        color: #cbd5e1;
    }
    .empty .big { font-size: 2.4rem; }
    div.stButton > button, div.stFormSubmitButton > button {
        border-radius: 10px;
        border: 1px solid #6477ff;
        background: #4f46e5;
        color: white;
        font-weight: 600;
        min-height: 42px;
    }
    div.stButton > button:hover, div.stFormSubmitButton > button:hover {
        background: #4338ca;
        border-color: #818cf8;
        color: white;
    }
    input, textarea, [data-baseweb="select"] > div {
        background-color: #101827 !important;
        color: #f8fafc !important;
        border-color: #334155 !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid #29364d;
        border-radius: 12px;
        overflow: hidden;
    }
    hr { border-color: #29364d; }
    </style>
    """,
    unsafe_allow_html=True,
)


def get_connection():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                phone TEXT DEFAULT '',
                role TEXT NOT NULL,
                skills TEXT DEFAULT '',
                experience REAL DEFAULT 0,
                education TEXT DEFAULT 'Other',
                status TEXT DEFAULT 'Applied',
                applied_on TEXT NOT NULL,
                notes TEXT DEFAULT ''
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS activity_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event TEXT NOT NULL,
                candidate_name TEXT DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )


def log_activity(event, candidate_name=""):
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO activity_log(event, candidate_name, created_at) VALUES (?, ?, ?)",
            (event, candidate_name, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )


def load_candidates():
    with get_connection() as conn:
        return pd.read_sql_query("SELECT * FROM candidates ORDER BY id DESC", conn)


def load_activity():
    with get_connection() as conn:
        return pd.read_sql_query(
            "SELECT event AS Activity, candidate_name AS Candidate, created_at AS Time "
            "FROM activity_log ORDER BY id DESC LIMIT 30",
            conn,
        )


def add_candidate(values):
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO candidates
            (name, email, phone, role, skills, experience, education, status, applied_on, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            values,
        )


def update_candidate(candidate_id, values):
    with get_connection() as conn:
        conn.execute(
            """
            UPDATE candidates
            SET name=?, email=?, phone=?, role=?, skills=?, experience=?,
                education=?, status=?, applied_on=?, notes=?
            WHERE id=?
            """,
            (*values, candidate_id),
        )


def delete_candidate(candidate_id):
    with get_connection() as conn:
        conn.execute("DELETE FROM candidates WHERE id=?", (int(candidate_id),))


def empty_state(icon, heading, detail):
    st.markdown(
        f"""
        <div class="empty">
          <div class="big">{icon}</div>
          <h3>{heading}</h3>
          <p>{detail}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


initialize_database()

with st.sidebar:
    st.markdown("## 💼 TalentDesk")
    st.caption("Recruitment & HR Analytics")
    st.divider()
    page = st.radio(
        "NAVIGATION",
        ["Dashboard", "Add Candidate", "Candidate Database", "Skill Matcher", "Activity Log", "About"],
        label_visibility="visible",
    )
    st.divider()
    st.caption("Dark workspace • Local SQLite database")
    st.caption(f"Database: {DB_PATH.name}")

candidates = load_candidates()

st.markdown(
    """
    <div class="hero">
      <h1>Recruitment & HR Analytics</h1>
      <p>Manage applicants, follow hiring progress, and find candidates whose skills match a role.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if page == "Dashboard":
    total = len(candidates)
    selected = int((candidates["status"] == "Selected").sum()) if total else 0
    interviews = int((candidates["status"] == "Interview").sum()) if total else 0
    shortlisted = int((candidates["status"] == "Shortlisted").sum()) if total else 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Candidates", total)
    c2.metric("Shortlisted", shortlisted)
    c3.metric("Interviews", interviews)
    c4.metric("Selected", selected)

    st.subheader("Hiring overview")
    if candidates.empty:
        empty_state(
            "🗂️",
            "No candidates added yet",
            "Your dashboard is ready. Use “Add Candidate” in the sidebar to create your first candidate entry. Your analytics will appear here automatically.",
        )
        st.write("")
        if st.button("＋ Add your first candidate", use_container_width=True):
            st.session_state["go_to_add"] = True
            st.rerun()
    else:
        left, right = st.columns(2)
        with left:
            st.markdown("#### Candidates by status")
            status_counts = (
                candidates["status"].value_counts()
                .reindex(STATUSES, fill_value=0)
                .rename_axis("Status")
                .reset_index(name="Candidates")
            )
            st.bar_chart(status_counts.set_index("Status"), color="#818cf8")
        with right:
            st.markdown("#### Applications by role")
            role_counts = candidates["role"].value_counts().head(8)
            st.bar_chart(role_counts, color="#34d399")
        st.markdown("#### Recently added candidates")
        display_cols = ["id", "name", "role", "experience", "status", "applied_on"]
        st.dataframe(
            candidates[display_cols].rename(
                columns={
                    "id": "ID", "name": "Name", "role": "Role",
                    "experience": "Experience (years)", "status": "Status", "applied_on": "Applied on"
                }
            ),
            use_container_width=True,
            hide_index=True,
        )

elif page == "Add Candidate":
    st.subheader("＋ Add a candidate")
    st.write("Enter candidate details below. Fields marked * are required.")
    with st.form("add_candidate_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full name *", placeholder="e.g. Aisha Sharma")
            email = st.text_input("Email address *", placeholder="name@example.com")
            phone = st.text_input("Phone number", placeholder="Optional")
            role = st.text_input("Role applied for *", placeholder="e.g. Python Developer")
            skills = st.text_input("Skills", placeholder="Python, SQL, communication")
        with col2:
            experience = st.number_input("Experience (years)", min_value=0.0, max_value=60.0, value=0.0, step=0.5)
            education = st.selectbox("Education", EDUCATION)
            status = st.selectbox("Application status", STATUSES)
            applied_on = st.date_input("Application date", value=date.today())
        notes = st.text_area("Notes", placeholder="Interview notes, strengths, or follow-up actions")
        submitted = st.form_submit_button("Save candidate", use_container_width=True)

    if submitted:
        if not name.strip() or not email.strip() or not role.strip():
            st.error("Please fill in Full name, Email address, and Role applied for.")
        elif "@" not in email or "." not in email.rsplit("@", 1)[-1]:
            st.error("Please enter a valid email address.")
        else:
            values = (
                name.strip(), email.strip().lower(), phone.strip(), role.strip(),
                skills.strip(), float(experience), education, status,
                applied_on.isoformat(), notes.strip(),
            )
            try:
                add_candidate(values)
                log_activity("Candidate added", name.strip())
                st.success(f"Candidate “{name.strip()}” was saved successfully.")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("That email address already exists. Use a different email address.")

elif page == "Candidate Database":
    st.subheader("Candidate database")
    if candidates.empty:
        empty_state("📭", "No entries to show", "The database is empty right now. Add a candidate first, then return here to search, edit, or delete records.")
    else:
        qcol1, qcol2 = st.columns([2, 1])
        with qcol1:
            search_text = st.text_input("Search candidates", placeholder="Search by name, email, role, or skills")
        with qcol2:
            status_filter = st.selectbox("Filter by status", ["All statuses"] + STATUSES)
        filtered = candidates.copy()
        if search_text.strip():
            term = search_text.strip().lower()
            searchable = filtered[["name", "email", "role", "skills"]].fillna("").astype(str)
            mask = searchable.apply(lambda col: col.str.lower().str.contains(term, regex=False)).any(axis=1)
            filtered = filtered[mask]
        if status_filter != "All statuses":
            filtered = filtered[filtered["status"] == status_filter]
        st.caption(f"Showing {len(filtered)} of {len(candidates)} candidate(s)")
        st.dataframe(
            filtered.rename(
                columns={
                    "id": "ID", "name": "Name", "email": "Email", "phone": "Phone",
                    "role": "Role", "skills": "Skills", "experience": "Experience (years)",
                    "education": "Education", "status": "Status", "applied_on": "Applied on", "notes": "Notes"
                }
            ),
            use_container_width=True,
            hide_index=True,
        )
        st.divider()
        st.markdown("#### Edit or delete a candidate")
        selected_id = st.selectbox(
            "Choose candidate",
            filtered["id"].tolist() if not filtered.empty else candidates["id"].tolist(),
            format_func=lambda cid: (
                f"#{int(cid)} — {candidates.loc[candidates['id'] == cid, 'name'].iloc[0]}"
            ),
        )
        chosen = candidates[candidates["id"] == selected_id].iloc[0]
        edit_tab, delete_tab = st.tabs(["✏️ Edit details", "🗑️ Delete record"])
        with edit_tab:
            with st.form("edit_candidate_form"):
                a, b = st.columns(2)
                with a:
                    e_name = st.text_input("Full name", value=str(chosen["name"]))
                    e_email = st.text_input("Email", value=str(chosen["email"]))
                    e_phone = st.text_input("Phone", value=str(chosen["phone"] or ""))
                    e_role = st.text_input("Role", value=str(chosen["role"]))
                    e_skills = st.text_input("Skills", value=str(chosen["skills"] or ""))
                with b:
                    e_exp = st.number_input("Experience (years)", min_value=0.0, max_value=60.0, value=float(chosen["experience"] or 0), step=0.5)
                    e_edu = st.selectbox("Education", EDUCATION, index=EDUCATION.index(chosen["education"]) if chosen["education"] in EDUCATION else EDUCATION.index("Other"))
                    e_status = st.selectbox("Status", STATUSES, index=STATUSES.index(chosen["status"]) if chosen["status"] in STATUSES else 0)
                    try:
                        e_date_default = date.fromisoformat(str(chosen["applied_on"]))
                    except ValueError:
                        e_date_default = date.today()
                    e_date = st.date_input("Application date", value=e_date_default)
                e_notes = st.text_area("Notes", value=str(chosen["notes"] or ""))
                save_edit = st.form_submit_button("Save changes", use_container_width=True)
            if save_edit:
                if not e_name.strip() or not e_email.strip() or not e_role.strip():
                    st.error("Name, email, and role are required.")
                else:
                    try:
                        update_candidate(
                            int(selected_id),
                            (e_name.strip(), e_email.strip().lower(), e_phone.strip(), e_role.strip(),
                             e_skills.strip(), float(e_exp), e_edu, e_status, e_date.isoformat(), e_notes.strip()),
                        )
                        log_activity("Candidate updated", e_name.strip())
                        st.success("Candidate updated.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("That email address is already assigned to another candidate.")
        with delete_tab:
            st.warning(f"You are about to delete {chosen['name']}'s record. This cannot be undone.")
            confirm_delete = st.checkbox("I understand and want to delete this record.")
            if st.button("Delete candidate", disabled=not confirm_delete):
                delete_candidate(int(selected_id))
                log_activity("Candidate deleted", str(chosen["name"]))
                st.success("Candidate deleted.")
                st.rerun()

elif page == "Skill Matcher":
    st.subheader("Skill matcher")
    st.write("Enter the skills required for a role. Candidates are ranked by the number of matching skills.")
    required_text = st.text_input("Required skills", placeholder="e.g. Python, SQL, machine learning")
    min_exp = st.slider("Minimum experience (years)", min_value=0.0, max_value=20.0, value=0.0, step=0.5)
    if candidates.empty:
        empty_state("🧩", "No candidates to match yet", "Add candidates with their skills and experience, then come back to find suitable matches.")
    elif not required_text.strip():
        st.info("Enter one or more skills above to start matching.")
    else:
        required = {skill.strip().lower() for skill in required_text.split(",") if skill.strip()}
        matches = []
        for _, row in candidates.iterrows():
            candidate_skills = {skill.strip().lower() for skill in str(row["skills"] or "").split(",") if skill.strip()}
            common = required.intersection(candidate_skills)
            if float(row["experience"] or 0) >= min_exp:
                matches.append({
                    "Name": row["name"],
                    "Role": row["role"],
                    "Experience (years)": row["experience"],
                    "Matched skills": ", ".join(sorted(common)) if common else "—",
                    "Match score (%)": round(len(common) / len(required) * 100),
                    "Status": row["status"],
                })
        results = pd.DataFrame(matches)
        if not results.empty:
            results = results.sort_values(["Match score (%)", "Experience (years)"], ascending=False)
            st.dataframe(results, use_container_width=True, hide_index=True)
            best = int(results["Match score (%)"].max())
            st.metric("Best skill match", f"{best}%")
            if best == 0:
                st.warning("No exact skill matches yet. Check spelling or add more skills to candidate profiles.")
        else:
            empty_state("🔎", "No candidates meet this filter", "Try lowering the minimum experience requirement.")

elif page == "Activity Log":
    st.subheader("Recent activity")
    activity = load_activity()
    if activity.empty:
        empty_state("🕘", "No activity yet", "Actions such as adding, editing, or deleting candidates will appear here.")
    else:
        st.dataframe(activity, use_container_width=True, hide_index=True)

elif page == "About":
    st.subheader("About TalentDesk")
    st.markdown(
        """
        <div class="panel">
          <h3>Recruitment & HR Analytics Portal</h3>
          <p>A lightweight candidate management application built with Python, Streamlit, Pandas, and SQLite.</p>
          <p><b>Features</b></p>
          <ul>
            <li>Add and store candidate profiles locally</li>
            <li>Search and filter the candidate database</li>
            <li>Edit or delete existing candidate records</li>
            <li>View hiring counts and charts on the dashboard</li>
            <li>Match candidates against required skills</li>
            <li>Review a log of recent changes</li>
          </ul>
          <p>Data is stored in a local SQLite database file named <code>recruitment_hr.db</code> in the same folder as this app.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.divider()
st.caption("TalentDesk • Recruitment & HR Analytics • Data saved locally on this computer")
