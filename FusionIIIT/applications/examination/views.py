from django.http import HttpResponse
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from applications.academic_information.models import Student

from .models import ExaminationAnnouncement, ReevaluationRequest, ResultPublication, SeatingPlan
from .permissions import IsAcadAdmin, IsDean, IsFaculty, IsStudent
from .selectors import (
    get_course_grade_summary_selector,
    get_dashboard_snapshot_selector,
    get_grade_audit_logs_selector,
    get_result_publication_status_selector,
    get_student_results_selector,
    get_student_semesters_selector,
    get_transcript_selector,
)
from .serializers import (
    AnnouncementSerializer,
    GradeSubmissionSerializer,
    PublishResultsSerializer,
    ReevaluationCreateSerializer,
    ReevaluationRequestSerializer,
    ReevaluationResolveSerializer,
    SeatingPlanCreateSerializer,
    SeatingPlanSerializer,
    UpdateGradeSerializer,
    VerifyGradesSerializer,
)
from .services import (
    create_announcement_service,
    generate_seating_plan_service,
    preview_grades_csv_service,
    publish_results_service,
    request_reevaluation_service,
    resolve_reevaluation_service,
    send_grade_deadline_reminders_service,
    submit_grades_service,
    sync_course_registrations_service,
    update_grade_service,
    upload_grades_csv_service,
    verify_grades_service,
)
from .utils import csv_template_response, generate_batch_result_excel, generate_marksheet_pdf, generate_transcript_pdf


class ExaminationDashboardView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(get_dashboard_snapshot_selector(request.user), status=status.HTTP_200_OK)


class FacultyCourseSyncView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsFaculty)

    def post(self, request):
        synced = sync_course_registrations_service(
            request.data.get("course_id"),
            request.data.get("semester_id"),
            request.data.get("academic_year"),
        )
        return Response({"synced_registrations": len(synced)}, status=status.HTTP_200_OK)


class SubmitGradesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsFaculty)

    def post(self, request):
        serializer = GradeSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        payload = serializer.validated_data
        submitted = submit_grades_service(
            request.user,
            payload["course_id"],
            payload["semester_id"],
            payload["academic_year"],
            payload["grades"],
        )
        return Response({"submitted": submitted}, status=status.HTTP_200_OK)


class PreviewGradesCSVView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsFaculty)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(preview_grades_csv_service(csv_file), status=status.HTTP_200_OK)


class UploadGradesCSVView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsFaculty)
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        csv_file = request.FILES.get("file")
        if not csv_file:
            return Response({"detail": "CSV file is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            uploaded = upload_grades_csv_service(
                request.user,
                request.data.get("course_id"),
                request.data.get("semester_id"),
                request.data.get("academic_year"),
                csv_file,
            )
        except ValueError as exc:
            return Response({"detail": str(exc)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"uploaded": uploaded}, status=status.HTTP_200_OK)


class DownloadGradeTemplateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsFaculty)

    def get(self, request):
        return csv_template_response()


class CourseGradeSummaryView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsFaculty)

    def get(self, request):
        return Response(
            get_course_grade_summary_selector(
                request.query_params.get("course_id"),
                request.query_params.get("semester_id"),
                request.query_params.get("academic_year"),
            ),
            status=status.HTTP_200_OK,
        )


class ValidateGradesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsDean)

    def get(self, request):
        return Response(
            get_course_grade_summary_selector(
                request.query_params.get("course_id"),
                request.query_params.get("semester_id"),
                request.query_params.get("academic_year"),
            ),
            status=status.HTTP_200_OK,
        )


class VerifyGradesView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsDean)

    def post(self, request):
        serializer = VerifyGradesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(verify_grades_service(request.user, **serializer.validated_data), status=status.HTTP_200_OK)


class UpdateGradeView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsDean)

    def post(self, request):
        serializer = UpdateGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        grade = update_grade_service(request.user, **serializer.validated_data)
        return Response({"student_id": grade.student_id_id, "new_grade": grade.letter_grade}, status=status.HTTP_200_OK)


class PublishResultsView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsAcadAdmin)

    def post(self, request):
        serializer = PublishResultsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        publication = publish_results_service(request.user, **serializer.validated_data)
        return Response({"publication_id": publication.id, "published_at": publication.published_at}, status=status.HTTP_200_OK)


class ResultPublicationStatusView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            get_result_publication_status_selector(
                request.query_params.get("batch_id"),
                request.query_params.get("semester_id"),
                request.query_params.get("academic_year"),
            ),
            status=status.HTTP_200_OK,
        )


class AnnouncementListCreateView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsAcadAdmin()]
        return [IsAuthenticated()]

    def get(self, request):
        return Response(AnnouncementSerializer(ExaminationAnnouncement.objects.all(), many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = AnnouncementSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        announcement = create_announcement_service(
            request.user,
            serializer.validated_data["title"],
            serializer.validated_data["message"],
            serializer.validated_data["audience"],
        )
        return Response(AnnouncementSerializer(announcement).data, status=status.HTTP_201_CREATED)


class StudentSemesterListView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsStudent)

    def get(self, request):
        student = Student.objects.get(id=request.user.extrainfo)
        return Response(get_student_semesters_selector(student), status=status.HTTP_200_OK)


class StudentResultView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsStudent)

    def get(self, request):
        student = Student.objects.get(id=request.user.extrainfo)
        return Response(
            get_student_results_selector(
                student,
                semester_id=request.query_params.get("semester_id"),
                academic_year=request.query_params.get("academic_year"),
            ),
            status=status.HTTP_200_OK,
        )


class StudentMarksheetDownloadView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsStudent)

    def get(self, request):
        student = Student.objects.get(id=request.user.extrainfo)
        payload = get_student_results_selector(
            student,
            semester_id=request.query_params.get("semester_id"),
            academic_year=request.query_params.get("academic_year"),
        )
        semester_key = "Semester {}".format(request.query_params.get("semester_no", ""))
        pdf_buffer = generate_marksheet_pdf(
            "{} - {}".format(student.id_id, student.id.user.get_full_name().strip() or student.id.user.username),
            payload["results"],
            payload["spi"].get(semester_key, 0),
            payload["cpi"],
        )
        response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="marksheet.pdf"'
        return response


class TranscriptView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        student_id = request.query_params.get("student_id")
        if student_id and IsAcadAdmin().has_permission(request, self):
            student = Student.objects.get(id=student_id)
        else:
            student = Student.objects.get(id=request.user.extrainfo)
        payload = get_transcript_selector(student)
        if request.query_params.get("format") == "pdf":
            pdf_buffer = generate_transcript_pdf(
                "{} - {}".format(payload["student_id"], payload["student_name"]),
                payload,
            )
            response = HttpResponse(pdf_buffer.getvalue(), content_type="application/pdf")
            response["Content-Disposition"] = 'attachment; filename="transcript.pdf"'
            return response
        return Response(payload, status=status.HTTP_200_OK)


class BatchResultExcelView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsAcadAdmin)

    def get(self, request):
        publication = ResultPublication.objects.filter(
            batch_id=request.query_params.get("batch_id"),
            semester_id=request.query_params.get("semester_id"),
            academic_year=request.query_params.get("academic_year"),
        ).first()
        result_rows = []
        if publication:
            for student in publication.batch.student_set.select_related("id__user").all():
                payload = get_student_results_selector(student, publication.semester_id, publication.academic_year, published_only=False)
                for row in payload["results"]:
                    result_rows.append(
                        {
                            "roll_no": student.id_id,
                            "student_name": student.id.user.get_full_name().strip() or student.id.user.username,
                            "course_code": row["course_code"],
                            "course_name": row["course_name"],
                            "credits": row["credits"],
                            "letter_grade": row["letter_grade"],
                            "grade_points": row["grade_points"],
                            "is_verified": row["is_verified"],
                        }
                    )
        workbook = generate_batch_result_excel(result_rows)
        response = HttpResponse(
            workbook.getvalue(),
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        response["Content-Disposition"] = 'attachment; filename="batch_results.xlsx"'
        return response


class ReevaluationRequestView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated(), IsStudent()]
        return [IsAuthenticated()]

    def get(self, request):
        queryset = ReevaluationRequest.objects.select_related("student", "course").all()
        if IsStudent().has_permission(request, self):
            queryset = queryset.filter(student_id=request.user.extrainfo.id)
        return Response(ReevaluationRequestSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = ReevaluationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(request_reevaluation_service(request.user, **serializer.validated_data), status=status.HTTP_201_CREATED)


class ReevaluationResolveView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsDean)

    def post(self, request):
        serializer = ReevaluationResolveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        request_obj = resolve_reevaluation_service(request.user, **serializer.validated_data)
        return Response(ReevaluationRequestSerializer(request_obj).data, status=status.HTTP_200_OK)


class GradeAuditLogView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        return Response(
            get_grade_audit_logs_selector(
                course_id=request.query_params.get("course_id"),
                student_id=request.query_params.get("student_id"),
            ),
            status=status.HTTP_200_OK,
        )


class SeatingPlanView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsAcadAdmin)

    def get(self, request):
        queryset = SeatingPlan.objects.filter(academic_year=request.query_params.get("academic_year", "")).order_by("exam_date", "hall_name")
        return Response(SeatingPlanSerializer(queryset, many=True).data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = SeatingPlanCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        plans = generate_seating_plan_service(request.user, **serializer.validated_data)
        return Response(SeatingPlanSerializer(plans, many=True).data, status=status.HTTP_201_CREATED)


class ReminderDispatchView(APIView):
    authentication_classes = (TokenAuthentication,)
    permission_classes = (IsAuthenticated, IsAcadAdmin)

    def post(self, request):
        reminders = send_grade_deadline_reminders_service(
            request.user,
            request.data.get("course_ids", []),
            request.data.get("deadline_label", "the grade deadline"),
        )
        return Response({"reminders": reminders}, status=status.HTTP_200_OK)
