from fastapi import Body
from fastapi_utils.cbv import cbv
from fastapi_utils.inferring_router import InferringRouter
from src.lib.utils.employee_utils import generate_employee_id, verify_employee_password, \
    create_employee_password_hashes
from src.web_api.models import ResponseModel
from src.data_classes.employee import Employee, PydanticEmployee, EmployeeHours, PydanticEmployeeHours
from src.lib import global_vars
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
router = InferringRouter()


@cbv(router)
class CoreRouter:
    @router.get("/api/v1/employees")
    async def get_employees(self):
        # List all the entries in employees table
        all_employees = []
        with global_vars.session_manager.make_session() as session:
            employees = session.query(Employee).all()
            for row in employees:
                item: Employee = row
                all_employees.append(item.as_dict())
        return ResponseModel(200, "success", {"employees": all_employees}).as_dict()

    @router.post("/api/v1/employees/new")
    async def post_new_employee(self, employee: PydanticEmployee):
        with global_vars.session_manager.make_session() as session:
            password_hash = create_employee_password_hashes(employee.RawPassword)
            employee_id = generate_employee_id(employee.FirstName.strip(),  employee.LastName.strip())
            try:
                # add_employee_query = text("CALL proc_add_employee(:id, :fName, :lName, :pHash)")
                # session.execute(add_employee_query, {
                #     "id": employee_id, "fName": employee.FirstName, "lName": employee.LastName,
                #     "pHash": password_hash
                # })
                new_employee = Employee(employee_id, employee.FirstName, employee.LastName, password_hash)
                session.add(new_employee)
                session.commit()
            except IntegrityError as e:
                raise Exception(str(e))
            created_employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).one()
        return ResponseModel(200, "success", {"employee": created_employee})

    @router.get("/api/v1/employees/hours")
    async def get_employee_hours(self, employee_id: str, date_start: str, date_end: str):
        with global_vars.session_manager.make_session() as session:
            try:
                # add_employee_query = text("CALL proc_add_employee(:id, :fName, :lName, :pHash)")
                # session.execute(add_employee_query, {
                #     "id": employee_id, "fName": employee.FirstName, "lName": employee.LastName,
                #     "pHash": password_hash
                # })
                total_hours = session.query(func.sum(EmployeeHours.HoursWorked).label('hours')).filter(
                    EmployeeHours.EmployeeID == employee_id,
                    EmployeeHours.DateWorked.between(date_start, date_end)
                ).scalar()
                print(total_hours)
            except IntegrityError as e:
                raise Exception(str(e))
        return ResponseModel(200, "success", {"hours": total_hours or 0})

    @router.post("/api/v1/employees/hours/add")
    async def post_employee_hours(self, employee_hours: PydanticEmployeeHours):
        with global_vars.session_manager.make_session() as session:
            try:
                work_hours_exists = session.query(EmployeeHours).filter(
                    EmployeeHours.EmployeeID == employee_hours.EmployeeID,
                    EmployeeHours.DateWorked == employee_hours.DateWorked
                ).all()
                if len(work_hours_exists) == 0:
                    total_employee_hours = EmployeeHours(
                        employee_hours.EmployeeID,
                        employee_hours.HoursWorked,
                        employee_hours.DateWorked
                    )
                    session.add(total_employee_hours)
                    session.commit()
                else:
                    raise Exception("Duplicate date entry! The employee already has hours entered for this day!")
            except IntegrityError as e:
                raise Exception(str(e))
            created_employee_hours = session.query(EmployeeHours).filter(
                EmployeeHours.EmployeeID == employee_hours.EmployeeID,
                EmployeeHours.DateWorked == employee_hours.DateWorked
            ).one()
        return ResponseModel(200, "success", {"employee_hours": created_employee_hours})

    @router.get("/api/v1/employees/count")
    async def get_employees_count(self):
        with global_vars.session_manager.make_session() as session:
            employees_count = session.query(Employee).count()
        return ResponseModel(200, "success", {"count": employees_count})

    @router.post("/api/v1/employees/verify")
    async def get_employee_password_verification(self, employee_id: str = Body(""), password_text: str = Body("")):
        with global_vars.session_manager.make_session() as session:
            employee = session.query(Employee).filter(Employee.EmployeeID == employee_id).one()
            employee_verified = verify_employee_password(password_text, employee.PasswordHash)
        return ResponseModel(200, "success", {"verified": employee_verified})
