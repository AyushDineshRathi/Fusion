from django.contrib import admin

from .models import (
    ExamCourseRegistration,
    ExaminationAnnouncement,
    GradeChangeLog,
    GradeComponent,
    ReevaluationRequest,
    ResultPublication,
    SeatingPlan,
    StudentComponentMark,
    StudentFinalGrade,
)


admin.site.register(ExamCourseRegistration)
admin.site.register(GradeComponent)
admin.site.register(StudentComponentMark)
admin.site.register(StudentFinalGrade)
admin.site.register(ResultPublication)
admin.site.register(GradeChangeLog)
admin.site.register(ReevaluationRequest)
admin.site.register(ExaminationAnnouncement)
admin.site.register(SeatingPlan)
