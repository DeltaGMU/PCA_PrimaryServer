from src.lib import global_vars


def verify_db_active() -> bool:
    if global_vars.session_manager.db_engine and global_vars.session_manager.session_factory:
        return True
    return False
