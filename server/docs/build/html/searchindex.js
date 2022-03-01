Search.setIndex({docnames:["api_employees","api_response_model","api_students","core_api","data_classes","database_manager","employee_data_class","employee_utils","error_codes","getting_started","index","installation","launch_parameters","logging_manager","manager_modules","print_utils","project_overview","project_resources","service_manager","strings","student_data_class","student_utils","utility_modules","web_api","web_manager","web_modules","web_service"],envversion:{"sphinx.domains.c":2,"sphinx.domains.changeset":1,"sphinx.domains.citation":1,"sphinx.domains.cpp":4,"sphinx.domains.index":1,"sphinx.domains.javascript":2,"sphinx.domains.math":2,"sphinx.domains.python":3,"sphinx.domains.rst":2,"sphinx.domains.std":2,sphinx:56},filenames:["api_employees.rst","api_response_model.rst","api_students.rst","core_api.rst","data_classes.rst","database_manager.rst","employee_data_class.rst","employee_utils.rst","error_codes.rst","getting_started.rst","index.rst","installation.rst","launch_parameters.rst","logging_manager.rst","manager_modules.rst","print_utils.rst","project_overview.rst","project_resources.rst","service_manager.rst","strings.rst","student_data_class.rst","student_utils.rst","utility_modules.rst","web_api.rst","web_manager.rst","web_modules.rst","web_service.rst"],objects:{"":[[0,0,1,"get--api-v1-employees","/api/v1/employees"],[0,0,1,"get--api-v1-employees-new","/api/v1/employees/new"]],"server.lib":[[5,1,0,"-","database_manager"],[8,1,0,"-","error_codes"],[13,1,0,"-","logging_manager"],[18,1,0,"-","service_manager"],[19,1,0,"-","strings"],[24,1,0,"-","web_manager"]],"server.lib.data_classes":[[6,1,0,"-","employee"],[20,1,0,"-","student"]],"server.lib.data_classes.employee":[[6,2,1,"","Employee"],[6,2,1,"","EmployeeHours"],[6,2,1,"","PydanticEmployee"],[6,2,1,"","PydanticEmployeeHours"]],"server.lib.data_classes.employee.Employee":[[6,3,1,"","EmployeeEnabled"],[6,3,1,"","EmployeeHoursRelationship"],[6,3,1,"","EmployeeID"],[6,3,1,"","EntryCreated"],[6,3,1,"","FirstName"],[6,3,1,"","LastName"],[6,3,1,"","PasswordHash"],[6,4,1,"","as_dict"],[6,3,1,"","id"]],"server.lib.data_classes.employee.EmployeeHours":[[6,3,1,"","DateWorked"],[6,3,1,"","EmployeeID"],[6,3,1,"","EntryCreated"],[6,3,1,"","HoursWorked"],[6,4,1,"","as_dict"],[6,3,1,"","id"]],"server.lib.data_classes.employee.PydanticEmployee":[[6,3,1,"","FirstName"],[6,3,1,"","LastName"],[6,3,1,"","RawPassword"]],"server.lib.data_classes.employee.PydanticEmployeeHours":[[6,3,1,"","DateWorked"],[6,3,1,"","EmployeeID"],[6,3,1,"","HoursWorked"]],"server.lib.data_classes.student":[[20,2,1,"","PydanticStudent"],[20,2,1,"","PydanticStudentCareHoursCheckIn"],[20,2,1,"","PydanticStudentCareHoursCheckOut"],[20,2,1,"","Student"],[20,2,1,"","StudentCareHours"]],"server.lib.data_classes.student.PydanticStudent":[[20,3,1,"","FirstName"],[20,3,1,"","LastName"],[20,3,1,"","StudentEnabled"]],"server.lib.data_classes.student.PydanticStudentCareHoursCheckIn":[[20,3,1,"","CareDate"],[20,3,1,"","CareType"],[20,3,1,"","CheckInTime"],[20,3,1,"","StudentID"]],"server.lib.data_classes.student.PydanticStudentCareHoursCheckOut":[[20,3,1,"","CareDate"],[20,3,1,"","CareType"],[20,3,1,"","CheckOutTime"],[20,3,1,"","StudentID"]],"server.lib.data_classes.student.Student":[[20,3,1,"","EntryCreated"],[20,3,1,"","FirstName"],[20,3,1,"","LastName"],[20,3,1,"","StudentCareHoursRelationship"],[20,3,1,"","StudentEnabled"],[20,3,1,"","StudentID"],[20,4,1,"","as_dict"],[20,3,1,"","id"]],"server.lib.data_classes.student.StudentCareHours":[[20,3,1,"","CareDate"],[20,3,1,"","CareType"],[20,3,1,"","CheckInTime"],[20,3,1,"","CheckOutTime"],[20,3,1,"","EntryCreated"],[20,3,1,"","StudentID"],[20,4,1,"","as_dict"],[20,3,1,"","id"]],"server.lib.database_manager":[[5,2,1,"","DatabaseManager"]],"server.lib.database_manager.DatabaseManager":[[5,4,1,"","get_engine"],[5,4,1,"","initialize"],[5,4,1,"","is_active"],[5,4,1,"","make_session"]],"server.lib.logging_manager":[[13,2,1,"","LoggingManager"]],"server.lib.logging_manager.LoggingManager":[[13,2,1,"","LogLevel"],[13,2,1,"","Settings"],[13,4,1,"","disable"],[13,4,1,"","enable"],[13,4,1,"","get_logger"],[13,4,1,"","initialize_logging"],[13,4,1,"","instance"],[13,4,1,"","is_enabled"],[13,4,1,"","log"]],"server.lib.logging_manager.LoggingManager.LogLevel":[[13,3,1,"","LOG_CRITICAL"],[13,3,1,"","LOG_DEBUG"],[13,3,1,"","LOG_ERROR"],[13,3,1,"","LOG_INFO"],[13,3,1,"","LOG_WARNING"],[13,4,1,"","has_value_id"],[13,4,1,"","has_value_label"]],"server.lib.logging_manager.LoggingManager.Settings":[[13,4,1,"","get_log_directory"],[13,4,1,"","get_log_level"],[13,4,1,"","get_max_log_size"],[13,4,1,"","get_max_logs"],[13,4,1,"","set_log_directory"],[13,4,1,"","set_log_level"],[13,4,1,"","set_max_log_size"],[13,4,1,"","set_max_logs"]],"server.lib.service_manager":[[18,2,1,"","SharedData"]],"server.lib.service_manager.SharedData":[[18,2,1,"","Managers"],[18,2,1,"","Settings"],[18,4,1,"","instance"]],"server.lib.service_manager.SharedData.Managers":[[18,4,1,"","get_database_manager"],[18,4,1,"","get_web_manager"],[18,4,1,"","set_database_manager"],[18,4,1,"","set_web_manager"]],"server.lib.service_manager.SharedData.Settings":[[18,4,1,"","get_debug_mode"],[18,4,1,"","get_quiet_mode"],[18,4,1,"","set_debug_mode"],[18,4,1,"","set_quiet_mode"]],"server.lib.utils":[[7,1,0,"-","employee_utils"],[15,1,0,"-","print_utils"],[21,1,0,"-","student_utils"]],"server.lib.utils.employee_utils":[[7,5,1,"","create_employee_password_hashes"],[7,5,1,"","generate_employee_id"],[7,5,1,"","verify_employee_password"]],"server.lib.utils.print_utils":[[15,5,1,"","console_print"],[15,5,1,"","debug_print"]],"server.lib.utils.student_utils":[[21,5,1,"","generate_student_id"]],"server.lib.web_manager":[[24,2,1,"","WebSessionManager"]],"server.lib.web_manager.WebSessionManager":[[24,4,1,"","initialize"],[24,4,1,"","start_web_server"],[24,4,1,"","stop_web_server"]],"server.services":[[26,1,0,"-","web_service"]],"server.services.web_service":[[26,2,1,"","UvicornServer"],[26,2,1,"","WebService"],[26,5,1,"","general_exception_handler"],[26,5,1,"","general_http_exception"],[26,5,1,"","general_request_validation_exception"],[26,5,1,"","general_validation_exception"],[26,5,1,"","serve_index"],[26,5,1,"","starlette_http_exception"]],"server.services.web_service.UvicornServer":[[26,4,1,"","install_signal_handlers"],[26,4,1,"","run_in_thread"]],"server.services.web_service.WebService":[[26,4,1,"","initialize_web"],[26,4,1,"","stop_web"]],"server.web_api":[[1,1,0,"-","models"]],"server.web_api.models":[[1,2,1,"","ResponseModel"]],"server.web_api.models.ResponseModel":[[1,4,1,"","add_data_dict"],[1,4,1,"","as_dict"],[1,4,1,"","update_data"]],"server.web_api.routing.v1.employees":[[0,1,0,"-","routing"]],"server.web_api.routing.v1.employees.routing":[[0,2,1,"","EmployeesRouter"]],"server.web_api.routing.v1.employees.routing.EmployeesRouter":[[0,4,1,"","add_employee_hours"],[0,4,1,"","create_new_employee"],[0,4,1,"","get_all_employees"],[0,4,1,"","get_employee_hours"],[0,4,1,"","get_employees_count"],[0,4,1,"","remove_employee"],[0,4,1,"","verify_employee_password"]],"server.web_api.routing.v1.students":[[2,1,0,"-","routing"]],"server.web_api.routing.v1.students.routing":[[2,2,1,"","StudentsRouter"]],"server.web_api.routing.v1.students.routing.StudentsRouter":[[2,4,1,"","check_in_student"],[2,4,1,"","check_out_student"],[2,4,1,"","create_new_student"],[2,4,1,"","get_all_students"],[2,4,1,"","get_students_count"]]},objnames:{"0":["http","get","HTTP get"],"1":["py","module","Python module"],"2":["py","class","Python class"],"3":["py","attribute","Python attribute"],"4":["py","method","Python method"],"5":["py","function","Python function"]},objtypes:{"0":"http:get","1":"py:module","2":"py:class","3":"py:attribute","4":"py:method","5":"py:function"},terms:{"0":[0,2,5,11,13,19,24],"01t09":0,"03":0,"1":[0,5,11,19,24],"10":[11,13],"10485760":11,"11":11,"12":0,"127":[5,24],"17":11,"19":11,"2":[0,11],"20":13,"200":0,"201":0,"2021":16,"2022":[0,11,16],"23":11,"29955":5,"2b":0,"3":11,"30":13,"300":0,"31":11,"4":11,"40":13,"404":26,"46":0,"5":11,"50":13,"56709":[11,24],"58":0,"65536":13,"7":11,"73":11,"8e55boitgu5prmgbaihxlsd6vkqrtp4k":0,"9":11,"byte":[12,13],"catch":26,"class":[0,1,2,3,5,10,13,18,24,26],"default":[5,12,13],"do":[6,13,15,19,20,26],"enum":13,"int":[1,6,13,24,26],"new":[0,2,5,6,7,11,13,20,21],"null":24,"return":[0,1,2,5,6,7,13,15,18,20,21,24,26],"true":[0,5,6,7,11,13,18,20],"try":[6,8,18,20],A:[0,1,2,5,6,7,13,20,26],For:[6,7,11,15,20,21],IN:[23,25],If:[0,1,2,5,12,13,15,18,24],In:18,It:[0,13,18,24,26],NOT:[15,19],Not:2,The:[0,1,2,5,6,7,8,9,12,13,15,16,18,19,20,21,24,26],These:16,With:16,abl:16,about:16,academi:16,access:[8,11],account:[12,16],accumul:0,action:13,activ:[13,24,26],ad:[0,7,21],add:[0,1,2],add_data_dict:1,add_employee_hour:0,addit:[1,18],address:[5,24],adhanom:16,after:[2,5,16],all:[0,1,2,12,13,19,26],allow:[0,2,18],alreadi:[0,2,24],also:[0,1,13],an:[0,1,2,6,7,8,11,13,15,16,20,26],ani:[0,1,2,5,13,18,19],api:[3,6,16,19,20,24,25,26],append:1,applic:[0,8,12,13,15,18,26],apt:11,ar:[0,1,2,6,7,8,12,16,20],arg:26,argument:[9,11],as_dict:[1,6,20],async:26,attempt:[0,6,13,18,20],attribut:[6,20],audit:12,authent:[0,7,11],automat:[2,16,26],avail:[0,1,2,12,13,16],base:[0,1,2,5,6,13,16,18,20,24,26],basemodel:[6,20],bcrypt:7,been:[0,2,13,18,24],befor:[2,13,16,18],being:[0,6,7,13,15,18,20,21],below:[13,16],bodi:[0,2],bool:[5,7,13,18,20,26],both:[0,13],bug:18,built:[13,16,24],calcul:[0,16],call:[18,26],can:[0,2,5,7,9,12,13,15,16,21],cannot:[0,5,18],care:[2,16,20],care_d:20,care_typ:20,cared:20,caretyp:20,cascad:0,caught:[8,26],caus:[0,18,26],cd:11,chang:19,check:[0,2,5,13,16,20],check_in_stud:2,check_out_stud:2,checkin_tim:20,checkintim:20,checkout_tim:20,checkouttim:20,child:16,childcar:[2,16],christian:16,classmethod:[13,18],clone:11,close:5,code:[1,3,6,17,20,26],codebas:[11,18],codebase_loc:11,com:11,compar:[0,7],compat:1,conduct:[0,2],configur:26,connect:[5,8,18],connector:11,consist:[0,2,16],consol:[12,13,15,18],console_print:15,constant:[3,8,10],constructor:[5,13,18,24,26],contain:[0,1,2,5,6,7,13,15,18,19,20,21,24,26],content:[0,1],convert:[6,20],copi:11,core:[11,17],correct:[0,7],count:[0,2],cours:0,cp:11,creat:[0,2,5,6,7,11,20,21],create_employee_password_hash:7,create_new_employe:0,create_new_stud:2,credenti:0,critic:[12,13],cs00:8,cs01:8,current:[13,18,26],dai:0,data:[0,1,2,3,10,26],data_class:[0,2,6,20],data_dict:1,databas:[0,2,3,6,7,8,12,14,18,19,20,21],database_manag:[5,18],databasemanag:[5,18],date:[0,2],date_end:0,date_start:0,date_work:6,datework:6,db00:8,db01:8,db_name:12,dd:0,debian:11,debug:[11,12,13,15,18],debug_mod:[11,18,19,26],debug_print:15,decl_api:[6,20],defin:[0,2,6,13,15,20],delet:0,delta:16,deltagmu:11,descript:26,desir:12,destroi:[0,2],detail:26,detect:8,dev:11,develop:[10,15,16,18],dict:[0,1,6,20],dictionari:[1,6,20],differ:[0,1,2],digest:7,dimitrik:16,direct:13,directli:18,directori:[11,12,13],disabl:[13,18],displai:[8,13,15],doc:11,document:[11,25],doe:[0,1,18],don:[5,18],done:0,dotenv:11,download:16,drag:11,drop:11,due:5,duplic:0,dure:[5,15,18],each:12,elleni:16,elwi:16,employe:[3,4,16,22,23,25],employee_hour:0,employee_id:[0,6],employee_util:7,employeeen:[0,6],employeehour:[0,6],employeehoursrelationship:6,employeeid:[0,6],employeesrout:0,empti:[0,11],enabl:[6,12,13,18,20],enable_log:[11,13,19],end:[0,1,2,18,24],endpoint:[0,2,26],engin:5,ensur:[6,20],enter:[0,12],entiti:[0,2,6,20],entri:[0,1],entrycr:[0,6,20],env:12,env_debug_mod:19,env_enable_log:19,env_log_directori:19,env_log_level:19,env_mariadb_databas:19,env_mariadb_host:19,env_mariadb_pass:19,env_mariadb_port:19,env_mariadb_us:19,env_max_log:19,env_max_log_s:19,env_quiet_mod:19,env_web_host:19,env_web_port:19,environ:[11,17,18],equal:[0,7],err_app_caught:8,err_app_unknown:8,err_db_caught:8,err_db_service_inact:8,err_logging_mngr_incorrect_param:8,err_logging_mngr_not_initi:8,err_session_mngr_incorrect_param:8,err_session_mngr_not_initi:8,err_web_service_incorrect_param:8,err_web_service_not_initi:8,err_web_session_mngr_incorrect_param:8,err_web_session_mngr_not_initi:8,error:[0,1,3,12,13,15,17,18,19,26],error_cod:[13,15],error_typ:[13,15],error_wrapp:26,establish:[5,24],event:[12,13,18],exampl:[0,5,6,7,15,20,21,24],exc:26,exc_messag:13,exceed:13,except:[8,13,26],exist:[0,1,5,12,13,18],extend:[6,20],extra:0,factori:5,fail:26,failur:2,fall:16,fals:[0,7,11,13,26],fastapi:[0,2,11,26],fault:26,field:[0,1,2],file:[8,11,12,13,18],find:18,finish:5,first:[0,2,7,16,21],first_nam:[7,21],first_name_initi:[7,21],firstnam:[0,6,20],flag:26,fname:[6,20],follow:12,format:[0,1,2,6,7,20,21,26],found:[0,9],from:[0,1,2,6,7,11,13,16,18,20,21,26],front:[0,1,18,24],full:11,full_last_nam:[7,21],furo:11,gener:[0,7,8,11,19,21,26],general_exception_handl:26,general_http_except:26,general_request_validation_except:26,general_validation_except:26,generate_employee_id:7,generate_student_id:21,generated_project_root_directori:19,georg:16,get:[0,10,11,18],get_all_employe:0,get_all_stud:2,get_database_manag:18,get_debug_mod:18,get_employee_hour:0,get_employees_count:0,get_engin:5,get_log_directori:13,get_log_level:13,get_logg:13,get_max_log:13,get_max_log_s:13,get_quiet_mod:18,get_students_count:2,get_web_manag:18,git:11,github:11,given:[7,13,21],global:[13,18],grant:7,gryder:16,ha:[0,2,11,13,18,24],handl:[0,2,13,26],handler:[13,26],has_value_id:13,has_value_label:13,hash:[0,7],help:[7,15,21],here:[9,11,13],highlight:[0,1,2],host:[5,12,18,26],hour:[0,6,16,20],hours_work:6,hourswork:6,http:[0,1,2,6,11,20,26],httpexcept:[0,2,26],id:[0,6,7,20,21],imag:16,implement:[2,23],improp:26,inact:8,includ:[0,2,26],incorrect:[0,7,8],incorrectli:2,independ:[6,20],index:[10,26],info:[11,12,13],inform:[0,2,5,13,16],initi:[5,6,13,18,20,24,26],initialize_log:13,initialize_web:26,input:16,insert:[1,2],instal:[9,10],install_signal_handl:26,instanc:[13,18],instanti:18,instead:[5,13,15],instruct:9,integ:13,integr:[16,18],interact:[0,2,24],interfac:[0,1,2,5,16,18,26],intern:[15,18,26],invalid:[0,2,5,7,13],invoic:16,ip:[5,12,24],is_act:5,is_en:13,jason:16,jerom:16,jinja2templ:26,john123:0,john:0,johnson:16,jsmith123:0,jsmith300:0,json:[0,1,6,20,26],jsonrespons:26,kei:1,know:[13,19],kwarg:26,last:[0,2,7,21,26],last_nam:[7,21],lastnam:[0,6,20],launch:[9,10,11],least:11,leav:0,level:[12,13],lib:[0,2,5,6,7,13,15,18,20,21,24],libmariadb3:11,libmariadb:11,librari:13,like:26,linux:11,list:[0,2,11,13,15],lm00:8,lm01:8,lname:[6,20],locat:12,log:[0,3,8,9,14,15,17,18],log_crit:13,log_debug:13,log_directori:[12,13,19],log_error:13,log_error_gener:19,log_error_unknown:19,log_info:13,log_level:[11,12,13,19],log_origin_api:19,log_origin_databas:19,log_origin_gener:19,log_origin_shutdown:19,log_origin_startup:19,log_typ:13,log_warn:13,log_warning_gener:19,logger:13,logging_manag:13,loggingmanag:13,logic:[0,2,5,13,24],login:16,loglevel:13,made:5,mai:[0,13,18,26],main:[6,20],make:[5,13,26],make_sess:5,manag:[3,8,10,17,26],manual:[6,11,20,26],mariadb:[5,6,11,12,18,20],mariadb_databas:[11,19],mariadb_host:[11,19],mariadb_pass:[11,19],mariadb_port:[11,19],mariadb_us:[11,19],mason:16,max:[12,13],max_log:[11,12,13,19],max_log_s:[11,12,19],max_siz:13,maximum:[12,13],mean:[0,2],member:16,messag:[0,1,12,13,15,18,26],meta_nam:19,meta_vers:19,metadata:17,method:[1,6,7,11,13,15,18,20,21,24,26],mkdir:11,mm:0,mode:[11,12,15,18],model:[0,2,23,25],modifi:[6,13,19,20,26],modul:[0,2,6,7,10,13,15,18,19,20,21,26],month:0,multipl:[0,7,13,15,18,21],must:[0,2,13],my_databas:5,my_db_ip_address:11,my_db_nam:11,my_db_password:11,my_db_port:11,my_db_us:11,name:[0,1,2,5,7,11,12,21],neat:16,need:[0,1,6,7,13,15,18,20],never:26,newli:[7,21],no_print:13,none:[1,5,7,13,15,18,20,21,24,26],normal:11,number:[0,2,12,13],object:[0,1,2,5,13,18,24,26],occur:[13,26],offici:11,ok:0,oldest:13,one:18,onli:[0,11,18],oper:[0,2],option:[1,9,11,13,15,20,26],origin:[13,15,26],orm:[5,6,20],other:[0,13,18,26],otherwis:[7,18,21],out:[2,16,20],output:[13,15],over:0,overrid:26,overtim:0,overview:[9,10],packag:11,page:[0,1,2,10,26],paramet:[0,1,2,5,7,8,9,10,11,13,15,18,21,24,26],parent:16,part:16,pass:[5,8,12,13],passlib:11,password:[0,5,7,11,12],password_hash:7,password_text:0,passwordhash:[0,6],path:13,path_to_project:11,payrol:16,pca:3,pca_primaryserv:11,pcaproject:19,pcaserv:11,perman:0,phash:6,pip:11,plain:[0,7],plain_password:7,pleas:[5,13,15,18,19,26],port:[5,12,24,26],pre:16,prepar:1,present:[0,12,13],prevent:[13,18],primari:13,print:[3,12,13,22],print_util:15,process:[0,13,26],product:18,progress:[23,25],project:[1,3,9,11],prompt:11,prove:7,provid:[0,1,2,5,7,13,16,18,24,26],pto:0,pydant:[0,2,6,11,20,26],pydanticemploye:[0,6],pydanticemployeehour:[0,6],pydanticstud:[2,20],pydanticstudentcarehourscheckin:[2,20],pydanticstudentcarehourscheckout:[2,20],python3:11,python:[11,16],queri:[5,6,20],quickbook:16,quiet:[11,12,15,18],quiet_mod:[11,18,19],r:11,rais:[0,1,2,5,13,18,24],ramisa:16,rang:0,rawpassword:[0,6],re:[13,19],receiv:[6,20],record:[0,2,6,7,20,21],refer:[0,2,5,13,15,18],referenc:[13,18],regard:2,regist:[0,2],relat:[0,2,7,15,21],remot:11,remov:0,remove_employe:0,replac:13,replic:[6,20],report:16,repositori:11,repres:[1,6,20],represent:[1,6,13,20],request:[0,1,2,6,20,26],requestvalidationerror:26,requir:[0,2,5,6,7,9,10,13,15,19,20,21,24],reserv:8,resha:16,resourc:[3,10],respond:1,respons:[0,2,6,18,20,23,25,26],responsemodel:[0,1,2],rest:[0,2,12,16,26],result:[2,26],retriev:[0,1,2,5,13,18,26],robert:16,root:[11,12,18],root_dir:19,rotat:13,rout:[0,2],router:[0,2],run:[11,15,24,26],run_in_thread:26,runtim:[13,18,19],runtimeerror:[1,5,13,24],s:[0,18],salina:16,salt:[0,7],same:0,search:10,second:16,send:0,sent:[5,6,20,26],serv:[1,7,8,13,15,18,21,26],serve_index:26,server:[0,1,2,5,6,7,9,11,12,13,15,16,18,20,21,24,26],server_db:5,server_host:5,server_ip:12,server_pass:5,server_port:[5,12],server_us:5,servic:[2,3,8,14,24,25],service_manag:18,session:[3,5,8,13,14,18],set:[13,18,26],set_database_manag:18,set_debug_mod:18,set_log_directori:13,set_log_level:13,set_max_log:13,set_max_log_s:13,set_quiet_mod:18,set_web_manag:18,setup:[9,10],shareddata:18,should:[0,5,13,18,24,26],shown:16,shutdown:19,sign:16,singl:[0,1],singleton:18,size:[12,13],sm00:8,sm01:8,smith:0,softwar:16,solut:16,specif:26,specifi:0,sphinx:11,spring:16,sqlalchemi:[5,6,11,20],ssl_cert:26,ssl_kei:26,stack:13,standard:1,starlett:26,starlette_http_except:26,start:[0,10,24],start_web_serv:24,startup:19,state:[18,26],statu:[0,1],stop:[24,26],stop_web:26,stop_web_serv:24,store:[0,12,13,18],str:[0,1,5,6,7,13,15,20,21,24,26],string:[3,13,15,17],structur:[6,20],student:[3,4,16,22,23,25],student_checkin:2,student_checkout:2,student_id:20,student_util:21,studentcarehour:20,studentcarehourscheckin:2,studentcarehoursrelationship:20,studenten:20,studentid:20,studentsrout:2,subclass:[6,18,20],submit:16,succeed:7,success:[0,1,7,21],successfulli:0,sudo:11,support:[11,18],suppress:12,sure:[5,13,18,26],system:[0,8,12,13,16],t:[5,18],tabl:[0,2,6,20],taken:13,task:[7,15,21],teacher:16,team:16,templat:26,termin:11,text:[0,7],th:18,thei:0,thi:[0,1,2,5,6,7,8,11,12,13,15,16,18,19,20,21,24,26],thread:26,through:[0,5,6,13,20],throughout:18,time:[0,2,12,13,18],timesheet:[0,16],total:0,trace:13,tradition:18,transact:[6,20],tupl:13,two:16,txt:11,type:[0,1,2,5,6,7,13,15,18,20,21,26],typeerror:18,ubuntu:11,uniniti:8,union:13,unique_record_id:[7,21],univers:16,unknown:8,unless:[13,18,19],unspecifi:12,up:11,updat:[0,1,2,20,26],update_data:1,upon:7,us:[0,1,5,6,7,8,12,13,15,18,20,21,24],usag:23,use_http:26,user:[7,12],usernam:[5,11,12],util:[1,3,6,10,11,13,18,20],uvicorn:[11,26],uvicornserv:26,v1:[0,2],valid:[0,6,20,26],validationerror:26,valu:[13,19],variabl:[17,18],variou:8,verif:7,verifi:[0,7],verify_employee_password:[0,7],view:13,visit:11,vs1yux3qygrr3puqhj0:0,wa:[0,2,13,26],want:11,warn:[12,13,19],web:[0,1,2,3,8,10,12,14,18],web_api:[0,1,2],web_host:[11,19],web_ip:[12,24],web_manag:[18,24],web_port:[11,12,19,24],web_servic:26,web_session_manag:18,webservic:26,websessionmanag:[18,24],week:0,welcom:3,well:13,were:0,what:[13,19],when:[1,6,7,20,21,26],where:[5,11,18],which:[0,1,5,12,13],who:16,window:11,within:[0,1,18,19],without:18,wm00:8,wm01:8,word:18,work:[16,23,25],would:0,ws00:8,ws01:8,year:0,yet:13,you:[11,13,19],your:[11,26],yyyi:0},titles:["Employees API - WORK IN PROGRESS","API Response Models - WORK IN PROGRESS","Students API - WORK IN PROGRESS","Developer Documentation","Data Class Modules","Database Manager","Employee Data Class","Employee Utility","Project Error Codes","Getting Started","Welcome to PCA Project\u2019s documentation!","Requirements and Installation","Launch Parameters","Logging Manager","Manager Modules","Print Utility","Project Overview","Project Resources and Constants","Service Manager","Project String Resources","Student Data Class","Student Utility","Utility Modules","Web API Documentation","Web Session Manager","Web Modules","Web Service Documentation"],titleterms:{"class":[4,6,20],IN:[0,1,2],addit:9,api:[0,1,2,23],argument:12,code:8,constant:[17,19],content:10,core:19,data:[4,6,20],databas:5,develop:3,document:[0,3,10,23,26],employe:[0,6,7],environ:19,error:8,get:9,implement:0,indic:10,inform:9,instal:11,launch:12,log:[12,13,19],manag:[5,13,14,18,19,24],metadata:19,model:1,modul:[3,4,14,22,25],option:12,overview:16,paramet:12,pca:10,print:15,progress:[0,1,2],project:[8,10,16,17,19],requir:11,resourc:[17,19],respons:1,s:10,servic:[18,26],session:24,setup:11,start:9,string:19,student:[2,20,21],tabl:10,usag:0,util:[7,15,21,22],variabl:19,web:[23,24,25,26],welcom:10,work:[0,1,2]}})