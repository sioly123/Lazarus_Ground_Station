import os
import logging

class Utils:

    session_path = None

    def __init__(self):
        pass

    @staticmethod
    def get_appdata_path():
        appdata = os.getenv('APPDATA')
        if not appdata:
            appdata = os.path.expanduser('~')

        lazarus_dir = os.path.join(appdata,
                                   'Lazarus_Ground_Station')
        os.makedirs(lazarus_dir, exist_ok=True)
        return lazarus_dir

    @staticmethod
    def create_session_directory():
        base_dir = Utils.get_appdata_path()
        base_name = "session"
        counter = 1
        session_dir = os.path.join(base_dir,
                                   f"{base_name}_{counter}")

        while os.path.exists(session_dir):
            counter += 1
            session_dir = os.path.join(base_dir,
                                       f"{base_name}_{counter}")

        os.makedirs(session_dir)
        Utils.session_path = session_dir
        return session_dir