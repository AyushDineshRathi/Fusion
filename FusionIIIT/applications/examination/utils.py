import csv
from collections import OrderedDict, defaultdict
from io import BytesIO, StringIO

from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


GRADE_POINT_MAP = OrderedDict(
    [
        ("O", 10),
        ("A+", 10),
        ("A", 9),
        ("B+", 8),
        ("B", 7),
        ("C+", 6),
        ("C", 5),
        ("D+", 4),
        ("D", 3),
        ("F", 2),
    ]
)


def normalise_grade(grade):
    grade_value = str(grade or "").strip().upper()
    if grade_value not in GRADE_POINT_MAP:
        raise ValueError("Unsupported grade '{}'".format(grade))
    return grade_value


def get_grade_points(letter_grade):
    return GRADE_POINT_MAP[normalise_grade(letter_grade)]


def calculate_spi(result_rows):
    total_weighted = 0.0
    total_credits = 0.0
    for row in result_rows:
        credits = float(row.get("credits", 0) or 0)
        points = float(row.get("grade_points", 0) or 0)
        total_weighted += credits * points
        total_credits += credits
    if total_credits == 0:
        return 0.0
    return round(total_weighted / total_credits, 2)


def calculate_cpi(grouped_results):
    all_rows = []
    for semester_results in grouped_results.values():
        all_rows.extend(semester_results)
    return calculate_spi(all_rows)


def parse_grades_csv(file_obj):
    raw_bytes = file_obj.read()
    decoded = raw_bytes.decode("utf-8-sig")
    reader = csv.DictReader(StringIO(decoded))
    rows = []
    for index, row in enumerate(reader, start=2):
        normalized = {str(key).strip().lower(): value for key, value in row.items()}
        rows.append(
            {
                "line_number": index,
                "roll_no": str(normalized.get("roll_no", "")).strip(),
                "letter_grade": str(
                    normalized.get("letter_grade") or normalized.get("grade") or ""
                ).strip(),
                "remarks": str(normalized.get("remarks", "")).strip(),
            }
        )
    return rows


def build_csv_preview(rows):
    preview_rows = []
    errors = []
    for row in rows:
        if not row["roll_no"]:
            errors.append("Line {} missing roll_no".format(row["line_number"]))
            continue
        try:
            grade = normalise_grade(row["letter_grade"])
        except ValueError as exc:
            errors.append("Line {} {}".format(row["line_number"], exc))
            continue
        preview_rows.append(
            {
                "line_number": row["line_number"],
                "roll_no": row["roll_no"],
                "letter_grade": grade,
                "remarks": row["remarks"],
            }
        )
    return {"rows": preview_rows, "errors": errors}


def csv_template_response():
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="grade_upload_template.csv"'
    writer = csv.writer(response)
    writer.writerow(["roll_no", "letter_grade", "remarks"])
    writer.writerow(["20BCS001", "A", "Excellent performance"])
    return response


def generate_transcript_pdf(student_label, transcript_payload):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Fusion ERP Transcript", styles["Title"]),
        Paragraph(student_label, styles["Heading2"]),
        Spacer(1, 12),
    ]
    for semester_label, rows in transcript_payload["semesters"].items():
        story.append(Paragraph(semester_label, styles["Heading3"]))
        table_data = [["Course", "Credits", "Grade", "Points"]]
        for row in rows:
            table_data.append(
                [row["course_code"], row["credits"], row["letter_grade"], row["grade_points"]]
            )
        table_data.append(["SPI", transcript_payload["spi"].get(semester_label, 0), "", ""])
        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#d9e7ff")),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ]
            )
        )
        story.extend([table, Spacer(1, 14)])
    story.append(Paragraph("CPI: {}".format(transcript_payload["cpi"]), styles["Heading3"]))
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_marksheet_pdf(student_label, marksheet_rows, spi_value, cpi_value):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = [
        Paragraph("Fusion ERP Marksheet", styles["Title"]),
        Paragraph(student_label, styles["Heading2"]),
        Spacer(1, 12),
    ]
    table_data = [["Course", "Credits", "Grade", "Verified"]]
    for row in marksheet_rows:
        table_data.append(
            [row["course_code"], row["credits"], row["letter_grade"], "Yes" if row["is_verified"] else "No"]
        )
    table_data.extend([["SPI", spi_value, "", ""], ["CPI", cpi_value, "", ""]])
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f0ead6")),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ]
        )
    )
    story.append(table)
    doc.build(story)
    buffer.seek(0)
    return buffer


def generate_batch_result_excel(result_rows, sheet_title="Batch Results"):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = sheet_title[:31]
    sheet.append(
        [
            "Roll No",
            "Student Name",
            "Course Code",
            "Course Name",
            "Credits",
            "Grade",
            "Grade Points",
            "Verified",
        ]
    )
    for row in result_rows:
        sheet.append(
            [
                row["roll_no"],
                row["student_name"],
                row["course_code"],
                row["course_name"],
                row["credits"],
                row["letter_grade"],
                row["grade_points"],
                "Yes" if row["is_verified"] else "No",
            ]
        )
    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    return output


def distribute_seats(students, halls):
    seat_allocations = []
    seat_cursor = 1
    remaining = list(students)
    for hall in halls:
        capacity = int(hall["capacity"])
        hall_students = remaining[:capacity]
        if not hall_students:
            continue
        seat_allocations.append(
            {
                "hall_name": hall["hall_name"],
                "hall_capacity": capacity,
                "seat_start": seat_cursor,
                "seat_end": seat_cursor + len(hall_students) - 1,
                "students": hall_students,
            }
        )
        seat_cursor += len(hall_students)
        remaining = remaining[capacity:]
    return seat_allocations


def group_results_for_transcript(rows):
    semesters = defaultdict(list)
    spi = {}
    for row in rows:
        semester_label = "Semester {}".format(row["semester_no"])
        semesters[semester_label].append(row)
    for semester_label, semester_rows in semesters.items():
        spi[semester_label] = calculate_spi(semester_rows)
    return {"semesters": dict(semesters), "spi": spi, "cpi": calculate_cpi(semesters)}
