from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

# 🛢️ MySQL Connection
conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='SQL@123',
    database='cgpa_calculator'
)
cursor = conn.cursor()

# 🔧 Grade to Point Mapping
grade_map = {
    'AA': 10, 'AB': 9, 'BB': 8, 'BC': 7,
    'CC': 6, 'CD': 5, 'DD': 4, 'FP': 0,
    'FA': 0, 'UFM': 0
}

# 🔧 Create Base Tables
def create_tables():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            student_id VARCHAR(20) PRIMARY KEY,
            name VARCHAR(100)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            subject_id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100),
            credits INT,
            type ENUM('theory', 'practical')
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cgpa (
            student_id VARCHAR(20) PRIMARY KEY,
            cgpa FLOAT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    conn.commit()

# 🆕 Create missing grade tables for existing subjects
def create_missing_grade_tables():
    cursor.execute("SELECT subject_id FROM subjects")
    subject_ids = cursor.fetchall()

    for (subject_id,) in subject_ids:
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS grades_subject_{subject_id} (
                student_id VARCHAR(20),
                grade VARCHAR(3),
                credits INT,
                FOREIGN KEY (student_id) REFERENCES students(student_id)
            )
        ''')
    conn.commit()
    print("✅ All grade tables created for existing subjects.")

create_tables()
create_missing_grade_tables()

# 🧾 Serve Frontend
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')

# 🧑‍🏫 Add Subject
@app.route('/add-subject', methods=['POST'])
def add_subject():
    data = request.get_json()
    name, credits, typ = data['name'], data['credits'], data['type']

    cursor.execute("INSERT INTO subjects (name, credits, type) VALUES (%s, %s, %s)", (name, credits, typ))
    conn.commit()

    cursor.execute("SELECT subject_id FROM subjects WHERE name=%s ORDER BY subject_id DESC LIMIT 1", (name,))
    subject_id = cursor.fetchone()[0]

    cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS grades_subject_{subject_id} (
            student_id VARCHAR(20),
            grade VARCHAR(3),
            credits INT,
            FOREIGN KEY (student_id) REFERENCES students(student_id)
        )
    ''')
    conn.commit()

    return f"Subject '{name}' added with grade table."

# 👩‍🎓 Add Student and Grades
@app.route('/add-student', methods=['POST'])
def add_student():
    data = request.get_json()
    student_id = data['student_id']
    name = data['name']
    grades = data['grades']

    cursor.execute("INSERT INTO students (student_id, name) VALUES (%s, %s)", (student_id, name))
    conn.commit()

    for item in grades:
        subject_id, grade = item['subject_id'], item['grade']
        cursor.execute("SELECT credits FROM subjects WHERE subject_id = %s", (subject_id,))
        credits = cursor.fetchone()[0]

        cursor.execute(f'''
            INSERT INTO grades_subject_{subject_id} (student_id, grade, credits)
            VALUES (%s, %s, %s)
        ''', (student_id, grade, credits))
    conn.commit()

    return f"Student {name} added with grades. Use /calculate-cgpa/{student_id} to calculate CGPA."

# 🧮 Calculate CGPA for One Student
@app.route('/calculate-cgpa/<student_id>', methods=['POST'])
def calculate_cgpa(student_id):
    cursor.execute("SELECT subject_id FROM subjects")
    subject_ids = cursor.fetchall()

    total_points, total_credits = 0, 0

    for (subject_id,) in subject_ids:
        table_name = f"grades_subject_{subject_id}"
        cursor.execute(f"SELECT grade, credits FROM {table_name} WHERE student_id = %s", (student_id,))
        row = cursor.fetchone()
        if row and row[0]:
            grade, credits = row
            point = grade_map.get(grade, 0)
            total_points += point * credits
            total_credits += credits

    cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0
    cursor.execute("REPLACE INTO cgpa (student_id, cgpa) VALUES (%s, %s)", (student_id, cgpa))
    conn.commit()

    return jsonify({"student_id": student_id, "cgpa": cgpa})

# 🔁 Calculate CGPA for All Students
@app.route('/calculate-cgpa-all', methods=['POST'])
def calculate_all_cgpa():
    cursor.execute("SELECT student_id FROM students")
    student_ids = cursor.fetchall()

    for (student_id,) in student_ids:
        calculate_cgpa(student_id)

    return "CGPA updated for all students."

# ✏️ Update Grade + Auto-Recalculate CGPA
@app.route('/update-grade', methods=['POST'])
def update_grade():
    data = request.get_json()
    student_id = data['student_id']
    subject_id = data['subject_id']
    new_grade = data['grade']

    table_name = f"grades_subject_{subject_id}"
    cursor.execute(f"UPDATE {table_name} SET grade = %s WHERE student_id = %s", (new_grade, student_id))
    conn.commit()

    return calculate_cgpa(student_id)

# 📋 Get CGPA of One Student
@app.route('/cgpa/<student_id>', methods=['GET'])
def get_cgpa(student_id):
    cursor.execute("SELECT * FROM cgpa WHERE student_id = %s", (student_id,))
    result = cursor.fetchone()
    if not result:
        return 'Not found', 404
    return jsonify({'student_id': result[0], 'cgpa': result[1]})

# 📋 Get CGPA of All Students
@app.route('/cgpa-all', methods=['GET'])
def get_all_cgpa():
    cursor.execute('''
        SELECT s.student_id, s.name, c.cgpa
        FROM students s
        JOIN cgpa c ON s.student_id = c.student_id
    ''')
    results = cursor.fetchall()
    return jsonify([{'student_id': r[0], 'name': r[1], 'cgpa': r[2]} for r in results])

# 🟢 Start Server
if __name__ == '__main__':
    app.run(debug=True)
