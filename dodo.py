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


def task_project1_setup():
    """
    Setup dependencies.

    Project #1 - PostgreSQL Auto Tuner
    https://15799.courses.cs.cmu.edu/spring2022/project1.html
    """

    return {
        "actions": [
            'doit --db-file=.runner.db action_selection_openspiel_build',
        ],
        "uptodate": [False],
        "verbosity": 2,
    }


def task_project1():
    """
    Generate actions.sql and config.json.

    Project #1 - PostgreSQL Auto Tuner
    https://15799.courses.cs.cmu.edu/spring2022/project1.html
    """

    return {
        "actions": [
            'rm -rf ./workload/current/',
            'mkdir -p ./workload/current/',
            # Naming: postgresql*.csv.
            'cp %(workload_csv)s ./workload/current/postgresql_workload.csv',
            'echo \'{"VACUUM": true}\' > config.json',
            'doit --db-file=.runner.db action_recommendation --database_game_args="--use_hypopg=False"',
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
