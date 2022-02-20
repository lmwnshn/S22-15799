# doit automatically picks up tasks as long as their unqualified name is prefixed with task_.
# Read the guide: https://pydoit.org/tasks.html

from dodos.action import *
from dodos.behavior import *
from dodos.benchbase import *
from dodos.ci import *
from dodos.forecast import *
from dodos.noisepage import *
from dodos.pilot import *
from dodos.project1 import *

from doit.action import CmdAction
from plumbum import local

def task_project1():
    """
    Generate actions.
    """
    def example_function(workload_csv, timeout):
        print(f"dodo received workload CSV: {workload_csv}")
        print(f"dodo received timeout: {timeout}")

    return {
        "actions": [
            'python3 ./forecast/preprocessor.py --query-log-folder %(workload_csv)s --output-parquet out.parquet.gzip --output-timestamp out.timestamp.txt',
            'PYTHONPATH=.:$PYTHONPATH python3 util/sql.py',
            example_function,
            'echo "SELECT 1;" > actions.sql',
            'echo "SELECT 2;" >> actions.sql',
            'echo \'{"VACUUM": true}\' > config.json',
        ],
        "uptodate": [False],
        "verbosity": 2,
        "params": [
            {
                "name": "workload_csv",
                "long": "workload_csv",
                "help": "The PostgreSQL workload to optimize for.",
                "default": None,
            },
            {
                "name": "timeout",
                "long": "timeout",
                "help": "The time allowed for execution before this dodo task will be killed.",
                "default": None,
            },
        ],
    }
