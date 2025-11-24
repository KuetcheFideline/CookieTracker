import platform
import os
import time
from datetime import datetime



def get_os_info():
    system_info = platform.uname()

    os_system = system_info.system

    if os_system == 'Linux':
        return os_system
    else:
        return os_system
    





def init_var_env()->None:
    if 'SCRIPT_RUN_COUNT_MOZ' not in os.environ :
        os.environ['SCRIPT_RUN_COUNT_MOZ'] = '0'

    # increment run count
    run_count = int(os.environ['SCRIPT_RUN_COUNT_MOZ']) + 1
    os.environ['SCRIPT_RUN_COUNT_MOZ'] = str(run_count)

    # Get the current time
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    if 'LAST_RUN_TIME' not in os.environ:
        os.environ['LAST_RUN_TIME'] = current_time
    else:
        last_run_time = os.environ['LAST_RUN_TIME']


