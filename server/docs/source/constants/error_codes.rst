Project Error Codes
===================

.. automodule:: server.lib.error_codes
   :members:
   :undoc-members:
   :show-inheritance:


.. code-block:: python

    # The error code for incorrect parameters passed to a session manager.
    ERR_SESSION_MNGR_INCORRECT_PARAMS = 'SM00'

    # The error code for trying to use an uninitialized session manager.
    ERR_SESSION_MNGR_NOT_INITIALIZED = 'SM01'

    # The error code for incorrect parameters passed to a web session manager.
    ERR_WEB_SESSION_MNGR_INCORRECT_PARAMS = 'WM00'

    # The error code for trying to use an uninitialized web session manager.
    ERR_WEB_SESSION_MNGR_NOT_INITIALIZED = 'WM01'

    # The error code for incorrect parameters passed to a logging manager.
    ERR_LOGGING_MNGR_INCORRECT_PARAMS = 'LM00'

    # The error code for trying to use an uninitialized logging manager.
    ERR_LOGGING_MNGR_NOT_INITIALIZED = 'LM01'

    # Generic error code for an unknown error in the application.
    ERR_APP_UNKNOWN = 'CS00'

    # Generic error code for a caught exception in the application.
    ERR_APP_CAUGHT = 'CS01'

    # The error code for trying to access an inactive database connection.
    ERR_DB_SERVICE_INACTIVE = 'DB00'

    # Generic error code for a caught exception in the database manager.
    ERR_DB_CAUGHT = 'DB01'

    # The error code for incorrect parameters passed to the web service.
    ERR_WEB_SERVICE_INCORRECT_PARAMS = 'WS00'

    # The error for trying to use an uninitialized web service.
    ERR_WEB_SERVICE_NOT_INITIALIZED = 'WS01'
