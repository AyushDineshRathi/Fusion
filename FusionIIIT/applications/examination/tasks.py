from .services import send_grade_deadline_reminders_service


def send_exam_deadline_reminders(actor, course_ids, deadline_label):
    return send_grade_deadline_reminders_service(actor, course_ids, deadline_label)
