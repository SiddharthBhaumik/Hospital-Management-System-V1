<h1>🏥 Hospital Management System — V1</h1>

<p>A role-based Flask web application for managing doctors, patients, departments, appointments, and treatment history.</p>

<h2>🚀 Steps for Setup</h2>

<ol>
  <li><b>Install Git CLI</b> on your Windows system.</li>
  <li><b>Create a GitHub account</b> using your IITM email ID.</li>
  <li>Go to <b>github.com</b> and <b>create a new repository</b> (set it as <b>Private</b>).</li>
  <li><b>Clone the repository</b> to your local system using:
    <pre><code>git clone &lt;your-repo-url&gt;</code></pre>
  </li>
  <li><b>Install dependencies</b> from <code>requirements.txt</code>:
    <pre><code>pip install -r requirements.txt</code></pre>
  </li>
  <li><b>Start the Flask server</b>:
    <pre><code>python app.py</code></pre>
  </li>
</ol>

<h2>⭐ Features</h2>

<h3>👨‍💼 Admin Features</h3>
<ul>
  <li>Dashboard shows total doctors, patients, and charts</li>
  <li>Admin auto-created programmatically (no admin signup)</li>
  <li>Add, update, or blacklist doctors</li>
  <li>Add, update, or blacklist patients</li>
  <li>Search doctorsby name and department &amp; patients by name, ID, or contact details</li>
  <li>View all upcoming and past appointments</li>
  <li>Create doctor login details</li>
  <li>Edit doctor and patient profiles</li>
  <li>Create and edit department</li>
</ul>

<h3>👨‍⚕️ Doctor Features</h3>
<ul>
  <li>Dashboard shows upcoming appointments and assigned patients</li>
  <li>Mark appointments as Completed or Cancelled</li>
  <li>Provide availability for the next 7 days</li>
  <li>Add diagnosis, prescriptions, tests, and notes</li>
  <li>View complete patient history</li>
</ul>

<h3>🧑‍🦱 Patient Features</h3>
<ul>
  <li>Register and log in</li>
  <li>Dashboard showing departments &amp; upcoming appointments</li>
  <li>View doctor availability for the next 7 days</li>
  <li>Book &amp; cancel appointments</li>
  <li>View treatment history</li>
  <li>Edit profile and login details</li>
</ul>

<h3>📅 Appointment System</h3>
<ul>
  <li>Prevents double bookings for the same doctor/date/time</li>
  <li>Status workflow: Booked → Completed → Cancelled</li>
  <li>For completed appointments diagnosis, prescription, tests, and notes get stored</li>
  <li>Doctors &amp; patients can view history anytime</li>
</ul>

<h2>🛠 Tech Stack</h2>

<h3>🔙 Backend</h3>
<ul>
  <li>Flask (Python Web Framework)</li>
  <li>Flask-Login (Authentication & Session Management)</li>
  <li>Flask-SQLAlchemy &amp; SQLAlchemy ORM (Database ORM)</li>
  <li>SQLite(Database)</li>
  <li>phonenumbers  &amp; email-validator (Validation)</li>
</ul>

<h3>🎨 Frontend</h3>
<ul>
  <li>HTML5</li>
  <li>Bootstrap 5 (UI Styling & Components)</li>
  <li>Jinja2 Templates (Server-side Rendering)</li>
  <li>Chart.js (Analytics & Visualizations)</li>
</ul>


<h2>📂 Project Structure</h2>

```plaintext
app.py
README.md
requirements.txt

controller/
├── admin_routes.py
├── config.py
├── doctor_routes.py
├── models.py
├── patient_routes.py
└── routes.py

instance/
└── database.db

templates/
├── base.html
├── home.html
├── patient_login.html
├── register.html
├── staff_login.html
│
├── Admin/
│   ├── admin_appointments.html
│   ├── admin_appt_view.html
│   ├── admin_dashboard.html
│   ├── admin_department.html
│   ├── admin_dept_create.html
│   ├── admin_dept_edit.html
│   ├── admin_doctors.html
│   ├── admin_doctor_create.html
│   ├── admin_doctor_edit.html
│   ├── admin_patients.html
│   ├── admin_patient_edit.html
│   └── base.html
│
├── Doctor/
│   ├── base.html
│   ├── doctor_availability.html
│   ├── doctor_change_login.html
│   ├── doctor_dashboard.html
│   ├── doctor_patient_history.html
│   └── doctor_treatment.html
│
└── Patient/
    ├── base.html
    ├── patient_book.html
    ├── patient_change_login.html
    ├── patient_dashboard.html
    ├── patient_deptdoc.html
    ├── patient_edit_profile.html
    └── patient_history.html
```


<h2>🧩 Data Models</h2>
<ul>
  <li>User</li>
  <li>Roles</li>
  <li>Patient</li>
  <li>Doctor</li>
  <li>Department</li>
  <li>Appointment</li>
  <li>Treatment</li>
  <li>DoctorAvailability</li>
  <li>TimeSlot</li>
</ul>




