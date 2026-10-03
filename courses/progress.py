"""
Progress tracking helpers.

Progress = (completed lectures + passed assignments) / (all lectures + all assignments)

Everything here is computed from the existing LectureProgress and
AssignmentSubmission tables, so no database migration is required.
"""
import uuid
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

from .models import (
    Assignment,
    AssignmentSubmission,
    Certificate,
    Lecture,
    LectureProgress,
)


@dataclass
class CourseProgress:
    total_lectures: int = 0
    done_lectures: int = 0
    total_assignments: int = 0
    passed_assignments: int = 0
    last_activity: Optional[Any] = None
    next_lecture: Optional[Any] = None

    @property
    def total(self):
        return self.total_lectures + self.total_assignments

    @property
    def done(self):
        return self.done_lectures + self.passed_assignments

    @property
    def percent(self):
        return int(round(100 * self.done / self.total)) if self.total else 0

    @property
    def status(self):
        if self.total and self.done >= self.total:
            return 'completed'
        if self.done == 0:
            return 'not_started'
        return 'in_progress'

    @property
    def status_label(self):
        return {
            'completed': 'Completed',
            'in_progress': 'In progress',
            'not_started': 'Not started',
        }[self.status]

    @property
    def lectures_left(self):
        return self.total_lectures - self.done_lectures


def _build(lectures, assignments, done, passed):
    """done = {lecture_id: timestamp}, passed = {assignment_id: timestamp}"""
    by_lecture = defaultdict(list)
    for a in assignments:
        by_lecture[a.after_lecture_id].append(a)

    p = CourseProgress(
        total_lectures=len(lectures),
        total_assignments=len(assignments),
    )
    p.done_lectures = sum(1 for l in lectures if l.id in done)
    p.passed_assignments = sum(1 for a in assignments if a.id in passed)

    stamps = list(done.values()) + list(passed.values())
    p.last_activity = max(stamps) if stamps else None

    for l in lectures:
        if l.id not in done or any(a.id not in passed for a in by_lecture.get(l.id, [])):
            p.next_lecture = l
            break
    return p


def progress_for_student(student, courses):
    """One student, many courses  ->  {course_id: CourseProgress} (4 queries total)."""
    course_ids = [c.id for c in courses]
    lectures = defaultdict(list)
    for l in Lecture.objects.filter(course_id__in=course_ids):
        lectures[l.course_id].append(l)
    assignments = defaultdict(list)
    for a in Assignment.objects.filter(course_id__in=course_ids):
        assignments[a.course_id].append(a)

    done = defaultdict(dict)
    for lid, cid, ts in LectureProgress.objects.filter(
        student=student, lecture__course_id__in=course_ids
    ).values_list('lecture_id', 'lecture__course_id', 'completed_at'):
        done[cid][lid] = ts

    passed = defaultdict(dict)
    for aid, cid, ts in AssignmentSubmission.objects.filter(
        student=student, is_correct=True, assignment__course_id__in=course_ids
    ).values_list('assignment_id', 'assignment__course_id', 'submitted_at'):
        passed[cid][aid] = ts

    return {
        cid: _build(lectures[cid], assignments[cid], done[cid], passed[cid])
        for cid in course_ids
    }


def progress_for_course(course, student_ids):
    """One course, many students  ->  {student_id: CourseProgress} (4 queries total)."""
    lectures = list(course.lectures.all())
    assignments = list(course.assignments.all())

    done = defaultdict(dict)
    for sid, lid, ts in LectureProgress.objects.filter(
        lecture__course=course, student_id__in=student_ids
    ).values_list('student_id', 'lecture_id', 'completed_at'):
        done[sid][lid] = ts

    passed = defaultdict(dict)
    for sid, aid, ts in AssignmentSubmission.objects.filter(
        assignment__course=course, student_id__in=student_ids, is_correct=True
    ).values_list('student_id', 'assignment_id', 'submitted_at'):
        passed[sid][aid] = ts

    return {
        sid: _build(lectures, assignments, done[sid], passed[sid])
        for sid in student_ids
    }


def course_overview(course, student_ids):
    """Summary numbers for the admin: average %, completed / in progress / not started."""
    per_student = progress_for_course(course, list(student_ids))
    values = list(per_student.values())
    n = len(values)
    return {
        'students': n,
        'avg_percent': int(round(sum(v.percent for v in values) / n)) if n else 0,
        'completed': sum(1 for v in values if v.status == 'completed'),
        'in_progress': sum(1 for v in values if v.status == 'in_progress'),
        'not_started': sum(1 for v in values if v.status == 'not_started'),
        'per_student': per_student,
    }


def unlocked_lecture_ids(lectures, done_ids, assignments_by_lecture, passed_ids):
    """
    Lectures open one after another: a lecture unlocks only when EVERY earlier
    lecture is completed and every assignment attached to it has been passed.
    """
    unlocked, ready = set(), True
    for l in lectures:
        if ready:
            unlocked.add(l.id)
        ready = ready and l.id in done_ids and all(
            a.id in passed_ids for a in assignments_by_lecture.get(l.id, [])
        )
    return unlocked


def generate_credential_id(course, student):
    return f"UCY-{course.id}-{student.id}-{uuid.uuid4().hex[:8].upper()}"


def certificate_pending(student, course):
    """
    True when the student has finished the course (100%) but the admin has
    not issued the certificate yet.  The certificate is issued manually by the
    admin, normally within 2 hours of completion.
    """
    if Certificate.objects.filter(student=student, course=course).exists():
        return False
    return progress_for_student(student, [course])[course.id].status == 'completed'
