Requirements and Installation
===============================

.. _installation_page:

Requirements
~~~~~~~~~~~~~~
This project requires at least Python 3.9 with support for up to Python 3.11, and has official support for Ubuntu/Debian/Windows.

Required python packages for core server:

* SQLAlchemy~=1.4.31
* passlib~=1.7.4
* pydantic~=1.9.0
* fastapi~=0.73.0
* fastapi-utils~=0.2.1
* uvicorn~=0.17.5
* python-dotenv~=0.19.2
* mariadb~=1.0.9

Required python packages for documentation generation:

* furo==2022.2.23
* sphinx==4.4.0

Other required packages:

* GTK-3 Runtime Environment for Windows Installations

Installation and Setup
~~~~~~~~~~~~~~~~~~~~~~~

1) Create an empty directory named 'PCAServer' where you want to install the server:
    * Ubuntu/Debian/Windows: ``mkdir <path_to_project>/PCAServer/``
2) Access the new project directory in a terminal:
    * Ubuntu/Debian/Windows: ``cd <path_to_project>/PCAServer/``
3) Copy the server files to the project directory:
    * Method 1: Clone the GitHub repository files (Requires Git to be installed):
        * Ubuntu/Debian/Windows: ``git clone https://github.com/DeltaGMU/PCA_PrimaryServer.git .``
        * Git will prompt you for your GitHub username/password for authenticating access.
    * Method 2: Manually copy the codebase:
        * Ubuntu/Debian: ``cp -a /<codebase_location>/. /<path_to_project>/PCAServer/``
        * Windows: Drag and drop the files from the remote directory to the ``PCAServer/`` directory.
4) Install the required python packages for the server and documentation:
    * ``pip install -r requirements.txt``
    * ``pip install -r docs/requirements.txt``
5) Install the MariaDB Connector (Linux Only):
    * Debian/Ubuntu: ``sudo apt-get install libmariadb3 libmariadb-dev``
6) Setup the server configuration file in the server configs directory.
    * ``<path_to_project>/PCAServer/server/configs/server_config.ini``
7) Run the server:
    * ``python3 PCAServer/``
