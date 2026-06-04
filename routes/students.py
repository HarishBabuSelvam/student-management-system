from flask import Blueprint, render_template, redirect, url_for, flash, request, send_file, make_response
from flask_login import login_required
from models.student import Student, db
from sqlalchemy import or_
from datetime import datetime
import io, csv

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER

students_bp = Blueprint('students', __name__)

DEPARTMENTS = ['CSE', 'IT', 'ECE', 'EEE', 'Mechanical', 'Civil', 'MBA', 'MCA']

@students_bp.route('/')
@login_required
def dashboard():
    total = Student.query.count()
    male = Student.query.filter_by(gender='Male').count()
    female = Student.query.filter_by(gender='Female').count()
    dept_count = db.session.query(Student.department, db.func.count(Student.id)).group_by(Student.department).all()
    recent = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    dept_data = {dept: count for dept, count in dept_count}
    return render_template('dashboard.html',
        total=total, male=male, female=female,
        dept_count=dept_count, dept_data=dept_data, recent=recent)

@students_bp.route('/students')
@login_required
def student_list():
    search = request.args.get('search', '')
    dept_filter = request.args.get('department', '')
    query = Student.query
    if search:
        query = query.filter(or_(
            Student.first_name.ilike(f'%{search}%'),
            Student.last_name.ilike(f'%{search}%'),
            Student.email.ilike(f'%{search}%'),
            Student.phone.ilike(f'%{search}%')
        ))
    if dept_filter:
        query = query.filter_by(department=dept_filter)
    students = query.order_by(Student.created_at.desc()).all()
    return render_template('students.html',
        students=students, search=search,
        dept_filter=dept_filter, departments=DEPARTMENTS)

@students_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
def add_student():
    if request.method == 'POST':
        email = request.form.get('email')
        if Student.query.filter_by(email=email).first():
            flash('Email already exists!', 'danger')
            return render_template('add_student.html', departments=DEPARTMENTS, data=request.form)
        dob_str = request.form.get('date_of_birth')
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        student = Student(
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            email=email,
            phone=request.form.get('phone'),
            department=request.form.get('department'),
            year=int(request.form.get('year')),
            gender=request.form.get('gender'),
            date_of_birth=dob,
            address=request.form.get('address')
        )
        db.session.add(student)
        db.session.commit()
        flash('Student added successfully!', 'success')
        return redirect(url_for('students.student_list'))
    return render_template('add_student.html', departments=DEPARTMENTS, data={})

@students_bp.route('/students/<int:id>')
@login_required
def student_detail(id):
    student = Student.query.get_or_404(id)
    return render_template('student_detail.html', student=student)

@students_bp.route('/students/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    if request.method == 'POST':
        email = request.form.get('email')
        existing = Student.query.filter_by(email=email).first()
        if existing and existing.id != id:
            flash('Email already used by another student!', 'danger')
            return render_template('edit_student.html', student=student, departments=DEPARTMENTS)
        student.first_name = request.form.get('first_name')
        student.last_name = request.form.get('last_name')
        student.email = email
        student.phone = request.form.get('phone')
        student.department = request.form.get('department')
        student.year = int(request.form.get('year'))
        student.gender = request.form.get('gender')
        student.address = request.form.get('address')
        dob_str = request.form.get('date_of_birth')
        if dob_str:
            student.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
        student.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Student updated!', 'success')
        return redirect(url_for('students.student_detail', id=id))
    return render_template('edit_student.html', student=student, departments=DEPARTMENTS)

@students_bp.route('/students/delete/<int:id>', methods=['POST'])
@login_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    db.session.delete(student)
    db.session.commit()
    flash('Student deleted.', 'success')
    return redirect(url_for('students.student_list'))

@students_bp.route('/students/pdf/<int:id>')
@login_required
def student_pdf(id):
    student = Student.query.get_or_404(id)
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []
    title_style = ParagraphStyle('T', parent=styles['Title'],
        fontSize=20, textColor=colors.HexColor('#1a56db'), spaceAfter=6)
    sub_style = ParagraphStyle('S', parent=styles['Normal'],
        fontSize=11, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER, spaceAfter=4)
    elements.append(Paragraph("STUDENT MANAGEMENT SYSTEM", title_style))
    elements.append(Paragraph("Sri Venkateswara College of Engineering", sub_style))
    elements.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %I:%M %p')}", sub_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a56db')))
    elements.append(Spacer(1, 0.4*inch))
    data = [
        ['Student ID', f'STU-{student.id:04d}'],
        ['Full Name', f'{student.first_name} {student.last_name}'],
        ['Email', student.email],
        ['Phone', student.phone],
        ['Department', student.department],
        ['Year', f'Year {student.year}'],
        ['Gender', student.gender],
        ['Date of Birth', str(student.date_of_birth) if student.date_of_birth else 'N/A'],
        ['Address', student.address or 'N/A'],
        ['Enrolled On', student.created_at.strftime('%B %d, %Y')],
    ]
    table = Table(data, colWidths=[4*cm, 12*cm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#eff6ff')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 11),
        ('TEXTCOLOR', (0,0), (0,-1), colors.HexColor('#1e40af')),
        ('PADDING', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,0), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf',
        as_attachment=True,
        download_name=f'student_{student.first_name}_{student.last_name}.pdf')

@students_bp.route('/students/pdf/all')
@login_required
def all_students_pdf():
    students = Student.query.order_by(Student.department, Student.first_name).all()
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
        rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    elements = []
    title_style = ParagraphStyle('T', parent=styles['Title'],
        fontSize=18, textColor=colors.HexColor('#1a56db'), spaceAfter=4)
    sub_style = ParagraphStyle('S', parent=styles['Normal'],
        fontSize=10, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER, spaceAfter=4)
    elements.append(Paragraph("ALL STUDENTS REPORT", title_style))
    elements.append(Paragraph("Sri Venkateswara College of Engineering", sub_style))
    elements.append(Paragraph(f"Total: {len(students)} | Generated: {datetime.now().strftime('%B %d, %Y')}", sub_style))
    elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#1a56db')))
    elements.append(Spacer(1, 0.3*inch))
    headers = ['#', 'Name', 'Department', 'Year', 'Email', 'Phone', 'Gender']
    table_data = [headers]
    for i, s in enumerate(students, 1):
        table_data.append([str(i), f'{s.first_name} {s.last_name}',
            s.department, f'Year {s.year}', s.email, s.phone, s.gender])
    table = Table(table_data, colWidths=[1*cm, 4*cm, 2.5*cm, 1.5*cm, 5*cm, 3*cm, 2*cm], repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1a56db')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f0f9ff')]),
        ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e5e7eb')),
        ('PADDING', (0,0), (-1,-1), 5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('ALIGN', (1,1), (1,-1), 'LEFT'),
        ('ALIGN', (4,1), (4,-1), 'LEFT'),
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype='application/pdf',
        as_attachment=True, download_name='all_students_report.pdf')

@students_bp.route('/students/export/csv')
@login_required
def export_csv():
    students = Student.query.order_by(Student.created_at.desc()).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID','First Name','Last Name','Email','Phone',
                     'Department','Year','Gender','Date of Birth','Address','Created At'])
    for s in students:
        writer.writerow([s.id, s.first_name, s.last_name, s.email, s.phone,
                         s.department, s.year, s.gender, s.date_of_birth, s.address, s.created_at])
    output.seek(0)
    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = 'attachment; filename=students.csv'
    return response