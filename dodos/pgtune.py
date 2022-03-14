import os

import doit
from doit.action import CmdAction
from plumbum import cmd

from dodos import VERBOSITY_DEFAULT, default_artifacts_path, default_build_path

ARTIFACTS_PATH = default_artifacts_path()
BUILD_PATH = default_build_path()

PGTUNE = BUILD_PATH / "pgtune"
PGTUNE_CONF = BUILD_PATH / "postgresql.pgtune.conf"
DEFAULT_PASS = "project1pass"
DEFAULT_DB = "project1db"
DEFAULT_USER = "project1user"


def task_pgtune_clone():
    """
    pgtune: clone Greg Smith's pgtune.
    """

    def repo_clone(repo_url, branch_name):
        cmd = f"git clone {repo_url} --branch {branch_name} --single-branch --depth 1 {BUILD_PATH}"
        return cmd

    return {
        "actions": [
            # Set up directories.
            f"mkdir -p {BUILD_PATH}",
            # Clone BenchBase.
            CmdAction(repo_clone),
            # Reset working directory.
            lambda: os.chdir(doit.get_initial_workdir()),
        ],
        "targets": [PGTUNE],
        "uptodate": [True],
        "verbosity": VERBOSITY_DEFAULT,
        "params": [
            {
                "name": "repo_url",
                "long": "repo_url",
                "help": "The repository to clone from.",
                "default": "https://github.com/gregs1104/pgtune.git",
            },
            {
                "name": "branch_name",
                "long": "branch_name",
                "help": "The name of the branch to checkout.",
                "default": "master",
            },
        ],
    }


def task_pgtune_tune():
    """
    pgtune: Apply Greg Smith's pgtune.
    """

    def alter_sql():
        with open(PGTUNE_CONF, "r") as f:
            for line in f:
                if "=" in line:
                    key, val = [s.strip() for s in line.split("=")]
                    sql = f"ALTER SYSTEM SET {key}='{val}'"
                    cmd = CmdAction(
                        f'PGPASSWORD={DEFAULT_PASS} psql --host=localhost --dbname={DEFAULT_DB} --username={DEFAULT_USER} --command="{sql}"'
                    )
                    cmd.execute()
                    print(cmd, cmd.out.strip(), cmd.err.strip())

    return {
        "actions": [
            f"touch {BUILD_PATH / 'postgresql.conf'}",
            (
                f"python2 {PGTUNE} "
                f"--input-config={BUILD_PATH / 'postgresql.conf'} "
                f"--output-config={PGTUNE_CONF} "
                # The --version parameter doesn't have support for newer versions of PostgreSQL.
                # f"--version=$(pg_config | grep VERSION | cut -d' ' -f 4) "
                f"--type=Mixed "
            ),
            alter_sql,
            lambda: cmd.sudo["systemctl"]["restart", "postgresql"].run_fg(),
            "until pg_isready ; do sleep 1 ; done",
        ],
        "file_dep": [PGTUNE],
        "uptodate": [False],
        "verbosity": VERBOSITY_DEFAULT,
    }


def task_pgtune_tune_more():
    """
    pgtune: Apply additional settings based on le0pard's PGTUNE.
    See: https://github.com/le0pard/pgtune/blob/master/assets/selectors/configuration.js
    """

    def alter_disk():
        disk = CmdAction("df /var/lib/postgresql/14/main | awk '{if (NR!=1) {print $1}}' | awk -F '/' '{print $NF}'")
        disk.execute()
        disk = disk.out.strip()

        is_hdd = CmdAction(f"lsblk -o NAME,ROTA | grep {disk} | awk -F ' ' '{{print $NF}}'")
        is_hdd.execute()
        is_hdd = is_hdd.out.strip() == "1"

        effective_io_concurrency = 0 if is_hdd else 200
        sql = f"ALTER SYSTEM SET effective_io_concurrency='{effective_io_concurrency}'"
        cmd = CmdAction(
            f'PGPASSWORD={DEFAULT_PASS} psql --host=localhost --dbname={DEFAULT_DB} --username={DEFAULT_USER} --command="{sql}"'
        )
        cmd.execute()
        print(cmd, cmd.out.strip(), cmd.err.strip())

    sql_list = [
        "ALTER SYSTEM SET min_wal_size='1GB'",
        "ALTER SYSTEM SET max_wal_size='4GB'",
    ]

    return {
        "actions": [
            *[
                f'PGPASSWORD={DEFAULT_PASS} psql --host=localhost --dbname={DEFAULT_DB} --username={DEFAULT_USER} --command="{sql}"'
                for sql in sql_list
            ],
            alter_disk,
            lambda: cmd.sudo["systemctl"]["restart", "postgresql"].run_fg(),
            "until pg_isready ; do sleep 1 ; done",
        ],
        "verbosity": VERBOSITY_DEFAULT,
    }
