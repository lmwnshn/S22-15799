# from pathlib import Path
#
# from doit.action import CmdAction

"""
Algorithm.

In the first iteration,
1. Reset index statistics. This allows us to track what indexes are actually used during workload execution.
2. Set simple hardware GUCs.

In each iteration,
1. Mark any indexes that were used.
2. Drop any indexes that are unused and/or unmarked.
3. Look at the workload and figure out what columns are used.
    3a. Generate index candidates.
    3b. Generate statistics.
4. Run database_game to try out index suggestions.

SELECT n_tup_upd, n_tup_hot_upd
FROM pg_stat_user_tables
WHERE schemaname = 'public'
  AND relname = 'jungle';

create index on jungle(uuid_field) with (fillfactor=50);
create index on jungle(int_field0) with (fillfactor=50);
create index on jungle(int_field1) with (fillfactor=50);
create index on jungle(int_field2) with (fillfactor=50);
create index on jungle(int_field3) with (fillfactor=50);
create index on jungle(int_field4) with (fillfactor=50);
create index on jungle(int_field5) with (fillfactor=50);
create index on jungle(int_field6) with (fillfactor=50);
create index on jungle(int_field7) with (fillfactor=50);
create index on jungle(int_field8) with (fillfactor=50);
create index on jungle(int_field9) with (fillfactor=50);
"""


def task_project1_setup():
    """
    Setup dependencies.

    Project #1 - PostgreSQL Auto Tuner
    https://15799.courses.cs.cmu.edu/spring2022/project1.html
    """

    return {
        "actions": [
            "doit --db-file=.runner.db pgtune_tune",
            "doit --db-file=.runner.db pgtune_tune_more",
            "doit --db-file=.runner.db action_selection_openspiel_build",
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

    # control_path = Path("./control").absolute()
    #
    # def actions():
    #     CmdAction("echo %(control_path)s")

    return {
        "actions": [
            "rm -rf ./workload/current/",
            "mkdir -p ./workload/current/",
            # Naming: postgresql*.csv.
            "cp %(workload_csv)s ./workload/current/postgresql_workload.csv",
            # actions,
            "echo '{\"VACUUM\": true}' > config.json",
            "doit --db-file=.runner.db action_recommendation",
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
