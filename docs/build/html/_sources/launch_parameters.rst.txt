Launch Parameters
===================

.. _launch_parameters_page:

Optional Arguments
~~~~~~~~~~~~~~~~~~~

  --host SERVER_IP      Enter the mariadb server IP using this parameter if a
                        .env file is not present.
  --port SERVER_PORT    Enter the mariadb server port using this parameter if
                        a .env file is not present.
  --user USER           Enter the username of the mariadb account using this
                        parameter if a .env file is not present.
  --pass PASSWORD       Enter the password of the mariadb account using this
                        parameter if a .env file is not present.
  --database DB_NAME    Enter the name of the mariadb database using this
                        parameter if a .env file is not present.
  --web-host WEB_IP     Enter the web server IP using this parameter if a .env
                        file is not present.
  --web-port WEB_PORT   Enter the desired REST server port using this
                        parameter if a .env file is not present.
  --enable-logs         Enables event logging which is useful to locate errors
                        and audit the system.
  --debug               Enables debug mode which prints event messages to the
                        console.
  --quiet               Enables quiet mode which suppresses all server event
                        messages.


Logging Arguments
~~~~~~~~~~~~~~~~~~~

  --log-level LOG_LEVEL
                        Enter the desired log level of logged events using
                        this parameter if a .env file is not present. The
                        following log levels are available to use: [debug,
                        info, warning, error, critical]
  --max-logs MAX_LOGS   Enter the maximum number of log files that can exist
                        at a time using this parameter if a .env file is not
                        present.
  --max-log-size MAX_LOG_SIZE
                        Enter the maximum size of each log file (in bytes)
                        using this parameter if a .env file is not present.
  --log-directory LOG_DIRECTORY
                        Enter the default directory to store log files using
                        this parameter if a .env file is not present. If
                        unspecified, the application uses "root/logs" to store
                        log files.