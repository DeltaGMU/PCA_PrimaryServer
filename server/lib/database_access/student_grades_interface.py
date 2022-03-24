from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from server.lib.data_classes.student_grade import StudentGrade, PydanticStudentGrade
from server.lib.database_manager import get_db_session
from sqlalchemy.exc import IntegrityError


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
