# Example: topics table should have columns (id, unit, topic_name)

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_from_directory, flash
import os
from reportlab.lib.pagesizes import letter
# Use ReportLab Platypus for nicer, styled PDFs
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
# ---------- ROUTES ----------

app = Flask(__name__)
app.secret_key = 'super_secret_key_please_change'  # Replace with a strong secret in production

# Route for syllabus page and PDF downloads
@app.route("/syllabus")
def syllabus():
    # Ensure syllabi directory exists
    syllabi_dir = os.path.join('static', 'syllabi')
    os.makedirs(syllabi_dir, exist_ok=True)
    return render_template('syllabus.html')

# PDF generation utility
def create_question_paper_pdf(data, filename):
    """Create a styled PDF using ReportLab Platypus and return the file path.

    The PDF is written to static/papers/<filename>. The function uses
    Paragraph styles for headings and body text and sets basic metadata.
    """
    pdf_path = os.path.join('static', 'papers', filename)
    os.makedirs(os.path.dirname(pdf_path), exist_ok=True)

    doc = SimpleDocTemplate(
        pdf_path,
        pagesize=letter,
        title=data.get('title', 'Question Paper'),
        author='QueMaster'
    )

    styles = getSampleStyleSheet()
    # Title style (centered)
    styles.add(ParagraphStyle(
        name='TitleStyle',
        parent=styles['Title'],
        fontName='Helvetica-Bold',
        fontSize=18,
        leading=22,
        alignment=1  # center
    ))
    styles.add(ParagraphStyle(
        name='Heading',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=13,
        leading=15,
    ))

    normal = styles['BodyText']

    story = []
    story.append(Paragraph(data.get('title', 'Question Paper'), styles['TitleStyle']))
    story.append(Spacer(1, 0.15 * inch))

    meta_lines = []
    meta_lines.append(f"Subject: {data.get('subject', '')}")
    meta_lines.append(f"Units: {data.get('unit', '')}")
    topics_list = ', '.join(data.get('topics', [])) if data.get('topics') else ''
    meta_lines.append(f"Topics: {topics_list}")
    meta_lines.append(f"Difficulty: {data.get('difficulty', '')}")
    meta_lines.append(f"Total Marks: {data.get('marks', '')}")

    for line in meta_lines:
        story.append(Paragraph(line, normal))
        story.append(Spacer(1, 0.05 * inch))

    story.append(Spacer(1, 0.2 * inch))

    def add_questions(label, questions, marks):
        story.append(Paragraph(label, styles['Heading']))
        story.append(Spacer(1, 0.05 * inch))
        for i, q in enumerate(questions, 1):
            if q:
                story.append(Paragraph(f"{i}. {q} [{marks} mark{'s' if marks > 1 else ''}]", normal))
                story.append(Spacer(1, 0.02 * inch))
        story.append(Spacer(1, 0.08 * inch))

    add_questions("Q1) Attempt any 4 of the following (1 mark each)", data.get('q1', []), 1)
    add_questions("Q2) Attempt any 4 of the following (2 marks each)", data.get('q2', []), 2)
    add_questions("Q3) Attempt any 2 of the following (4 marks each)", data.get('q3', []), 4)
    add_questions("Q4) Attempt any 1 of the following (5 marks)", data.get('q4', []), 5)

    doc.build(story)
    return pdf_path
@app.route('/get-topics')
def get_topics():
    unit_id = request.args.get('unit_id')
    print(f"[DEBUG] /get-topics called with unit_id={unit_id}")
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT topic_id, topic_name FROM topic WHERE unit_id=%s", (unit_id,))
    topics = [{'id': row[0], 'name': row[1]} for row in cur.fetchall()]
    print(f"[DEBUG] Topics returned: {topics}")
    cur.close()
    conn.close()
    return jsonify({'topics': topics})


@app.route('/get-units')
def get_units():
    subject_id = request.args.get('subject_id')
    conn = db_connection()
    cur = conn.cursor()
    # unit table uses unit_id, unit_name, weightage and sub_id FK
    cur.execute("SELECT unit_id, unit_name, weightage FROM unit WHERE sub_id=%s", (subject_id,))
    units = [{'id': row[0], 'name': row[1], 'weightage': row[2]} for row in cur.fetchall()]
    cur.close()
    conn.close()
    return jsonify({'units': units})

@app.route('/generate-paper', methods=['GET', 'POST'])
def generate_paper():
    data = request.get_json()
    subject = data.get('subject')
    topics = data.get('topics', [])
    difficulty = data.get('difficulty')
    marks = data.get('marks')
    title = data.get('title')
    unit = ', '.join(topics)  # For demo, treat topics as units
    # Collect questions
    q1 = [data.get(f'q1_{i}') for i in range(1, 6)]
    q2 = [data.get(f'q2_{i}') for i in range(1, 6)]
    q3 = [data.get(f'q3_{i}') for i in range(1, 4)]
    q4 = [data.get(f'q4_{i}') for i in range(1, 3)]

    paper_data = {
        'subject': subject,
        'topics': topics,
        'difficulty': difficulty,
        'marks': marks,
        'title': title,
        'unit': unit,
        'q1': q1,
        'q2': q2,
        'q3': q3,
        'q4': q4
    }
    filename = f"paper_{subject}_{title}.pdf".replace(' ', '_')
    pdf_path = create_question_paper_pdf(paper_data, filename)
    pdf_url = url_for('static', filename=f"papers/{filename}")
    return jsonify({'pdf_url': pdf_url})


# (imports consolidated at top)

# ---------- DATABASE CONNECTION ----------
def db_connection():
    conn = psycopg2.connect(
        dbname="quemaster_db",
        user="postgres",
        password="",  # actual PostgreSQL password
        host="localhost",
        port="5432" 
    )
    return conn

# ---------- ROUTES ----------

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/home')
def home():
    return render_template("home.html")

@app.route('/faq')
def faq():
    return render_template("faq.html")

@app.route('/about')
def about():
    return render_template("about.html")




@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM teacher WHERE email=%s", (email,))
        teacher = cur.fetchone()

        if teacher and check_password_hash(teacher[4], password):
            session["teacher_id"] = teacher[0]
            session["teacher_name"] = teacher[1]
            cur.close()
            conn.close()
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials. Please check your email and password.", "danger")
            cur.close()
            conn.close()
            return redirect(url_for('login'))

    return render_template("login.html")

@app.route('/signup', methods=["GET", "POST"])
def signup():
    conn = None
    cur = None
    error = None
    if request.method == "POST":
        try:
            conn = db_connection()
            cur = conn.cursor()
            name = request.form["name"]
            email = request.form["email"]
            subject = request.form["subject"]
            password = generate_password_hash(request.form["password"])

            # Check if account with this email already exists
            cur.execute("SELECT teacher_id FROM teacher WHERE email=%s", (email,))
            existing = cur.fetchone()
            if existing:
                flash("An account with this email already exists. Please login or use a different email.", "danger")
                return redirect(url_for('signup'))

            cur.execute(
                "INSERT INTO teacher (name, email, subject, password) VALUES (%s, %s, %s, %s)",
                (name, email, subject, password)
            )
            conn.commit()
            flash("Account created! Please log in.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            if conn:
                conn.rollback()
            error = f"Error: {e}"
            flash(error, "danger")
        finally:
            if cur:
                cur.close()
            if conn:
                conn.close()

    return render_template("signup.html", error=error)

@app.route('/dashboard')
def dashboard():
    if "teacher_id" not in session:
        return redirect(url_for('login'))
    
    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM subject")
    subjects = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("dashboard.html", subjects=subjects)


@app.route("/generate", methods=["GET", "POST"])
def generate():
    if "teacher_id" not in session:
        return redirect(url_for("login"))

    conn = db_connection()
    cur = conn.cursor()
    cur.execute("SELECT sub_id, sub_name FROM subject")
    subjects = cur.fetchall()
    cur.close()
    conn.close()


    if request.method == "POST":
        subject = request.form.get("subject")
        unit = request.form.get("unit")
        topics = request.form.getlist("topics")
        # Debug: print received values to server console to verify client submission
        print(f"[DEBUG] /generate POST received - subject={subject}, unit={unit}, topics={topics}")
        difficulty = request.form.get("difficulty")
        marks = request.form.get("marks")
        title = request.form.get("title")
        q1 = [request.form.get(f"q1_{i}") for i in range(1,6)]
        q2 = [request.form.get(f"q2_{i}") for i in range(1,6)]
        q3 = [request.form.get(f"q3_{i}") for i in range(1,4)]
        q4 = [request.form.get(f"q4_{i}") for i in range(1,3)]

        # Build paper data and create styled PDF
        paper_data = {
            'subject': subject,
            'topics': topics,
            'difficulty': difficulty,
            'marks': marks,
            'title': title,
            'unit': unit,
            'q1': q1,
            'q2': q2,
            'q3': q3,
            'q4': q4
        }
        # create safe filename
        safe_title = (title or 'paper').replace(' ', '_')
        safe_subject = (str(subject) if subject else 'subject').replace(' ', '_')
        filename = f"paper_{safe_subject}_{safe_title}.pdf"
        try:
            pdf_path = create_question_paper_pdf(paper_data, filename)
            pdf_url = url_for('static', filename=f"papers/{filename}")
            print(f"[DEBUG] PDF created at: {pdf_path}")
        except Exception as e:
            pdf_url = None
            print(f"[ERROR] Failed to create PDF: {e}")

        return render_template(
            "generate_success.html",
            subject=subject,
            unit=unit,
            topics=topics,
            difficulty=difficulty,
            marks=marks,
            title=title,
            q1=q1,
            q2=q2,
            q3=q3,
            q4=q4,
            pdf_url=pdf_url
        )

    return render_template("generate.html", subjects=subjects)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# ---------- RUN ----------
if __name__ == "__main__":
    app.run(debug=True)