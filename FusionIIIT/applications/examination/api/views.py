def parse_academic_year(academic_year, semester_type):
    """
    Legacy compatibility helper retained for modules that still import
    `applications.examination.api.views.parse_academic_year`.

    Returns `(working_year, normalized_academic_year)`.
    """
    academic_year = str(academic_year or "").strip()
    if not academic_year:
        raise ValueError("academic_year is required")

    if "-" in academic_year:
        start_year = int(academic_year.split("-")[0])
    else:
        start_year = int(academic_year)

    if semester_type == "Even Semester":
        return start_year + 1, academic_year
    return start_year, academic_year
