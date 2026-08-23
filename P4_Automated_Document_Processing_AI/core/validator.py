def validate(result, source):
    issues = []
    if not result.title.strip():
        issues.append("Title is missing.")
    if not result.summary.strip():
        issues.append("Summary is missing.")
    if not 0 <= result.confidence <= 1:
        issues.append("Confidence is outside 0-1.")
    if len(source.strip()) < 20:
        issues.append("Source is too short for reliable extraction.")
    return len(issues) == 0, issues
