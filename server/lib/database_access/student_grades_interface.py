from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from server.lib.data_classes.student_grade import StudentGrade, PydanticStudentGrade
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError


async def retrieve_all_grades(session: Session = None):
    if session is None:
        session = next(get_db_session())
    all_grades = session.query(StudentGrade).all()
    return all_grades


async def retrieve_one_grade(grade_name: str, session: Session = None):
    if grade_name is None or len(grade_name) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The provided student grade is invalid or empty!")
    if session is None:
        session = next(get_db_session())
    grade_name = grade_name.lower().strip()
    matching_grade = session.query(StudentGrade).filter(
        StudentGrade.Name == grade_name
    ).first()
    if matching_grade is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade information for the student could not be created due to invalid parameters!")
    return matching_grade


async def create_student_grade(student_grade: PydanticStudentGrade, session: Session = None):
    student_grade = student_grade.student_grade
    if len(student_grade) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade name cannot be empty!")
    if session is None:
        session = next(get_db_session())
    student_grade = student_grade.lower().strip()
    grade_exists = session.query(StudentGrade).filter(StudentGrade.Name == student_grade).first()
    if grade_exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"The student grade: '{student_grade}' already exists!")
    try:
        new_student_grade = StudentGrade(student_grade)
        session.add(new_student_grade)
        session.commit()
    except IntegrityError as err:
        session.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err
    return new_student_grade


async def remove_student_grade(student_grade: PydanticStudentGrade, session: Session = None):
    student_grade = student_grade.student_grade
    if len(student_grade) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="The student grade name cannot be empty!")
    if session is None:
        session = next(get_db_session())
    return {}
