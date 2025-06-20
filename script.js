const baseUrl = "http://localhost:5000";

// Toast Notification
function showToast(message, type = "info") {
  const toast = document.createElement("div");
  toast.className = `toast ${type}`;
  toast.innerText = message;

  document.getElementById("toast-container").appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

// Add Subject
document.getElementById("add-subject-form").onsubmit = async (e) => {
  e.preventDefault();
  const body = {
    name: document.getElementById("subjectName").value,
    credits: parseInt(document.getElementById("credits").value),
    type: document.getElementById("type").value
  };
  const res = await fetch(`${baseUrl}/add-subject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const text = await res.text();
  showToast(text, "success");
  e.target.reset();
};

// Add Student
document.getElementById("add-student-form").onsubmit = async (e) => {
  e.preventDefault();
  try {
    const body = {
      student_id: document.getElementById("studentId").value,
      name: document.getElementById("studentName").value,
      grades: JSON.parse(document.getElementById("gradesJson").value)
    };
    const res = await fetch(`${baseUrl}/add-student`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    });
    const text = await res.text();
    showToast(text, "success");
    e.target.reset();
  } catch {
    showToast("Invalid JSON Format", "error");
  }
};

// Calculate CGPA
document.getElementById("calc-cgpa-form").onsubmit = async (e) => {
  e.preventDefault();
  const studentId = document.getElementById("calcStudentId").value;
  const resultDiv = document.getElementById("cgpaResult");
  resultDiv.innerHTML = `<div class="spinner"></div>`;

  const res = await fetch(`${baseUrl}/calculate-cgpa/${studentId}`, {
    method: "POST"
  });
  const data = await res.json();
  resultDiv.innerHTML = `<strong>Student:</strong> ${data.student_id} <br><strong>CGPA:</strong> ${data.cgpa}`;
  resultDiv.scrollIntoView({ behavior: "smooth" });
};

// Batch CGPA
async function calculateAllCgpa() {
  const res = await fetch(`${baseUrl}/calculate-cgpa-all`, {
    method: "POST"
  });
  const text = await res.text();
  showToast(text, "info");
}

// Show All CGPA
async function showAllCgpa() {
  const res = await fetch(`${baseUrl}/cgpa-all`, {
    method: "GET"
  });
  const data = await res.json();
  let html = `<table><tr><th>Student ID</th><th>Name</th><th>CGPA</th></tr>`;
  data.forEach(d => {
    html += `<tr><td>${d.student_id}</td><td>${d.name}</td><td>${d.cgpa}</td></tr>`;
  });
  html += `</table>`;
  document.getElementById("cgpaTable").innerHTML = html;
  document.getElementById("cgpaTable").scrollIntoView({ behavior: "smooth" });
}

// Update Grade
async function updateGrade() {
  const body = {
    student_id: document.getElementById("updateStudentId").value,
    subject_id: parseInt(document.getElementById("updateSubjectId").value),
    grade: document.getElementById("updateGrade").value
  };
  const res = await fetch(`${baseUrl}/update-grade`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body)
  });
  const text = await res.text();
  showToast("Grade updated and CGPA recalculated", "success");
}
