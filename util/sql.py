
from dataclasses import dataclass
import json

import itertools
from pprint import pprint
import pglast.parser

import psycopg

from forecast.preprocessor import Preprocessor


@dataclass
class Column:
    name: str
    dtype: str
    active: bool = False

def get_catalog():
    query = "SELECT table_name, column_name, udt_name FROM information_schema.columns where table_schema='public';"
    catalog = {}
    with psycopg.connect("dbname=project1db user=project1user password=project1pass") as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            res = cur.fetchall()
            for table, col, dtype in res:
                catalog[table] = catalog.get(table, [])
                catalog[table].append(Column(col, dtype))
    return catalog


def item_generator(json_input, lookup_key):
    if isinstance(json_input, dict):
        for k, v in json_input.items():
            if k == lookup_key:
                yield v
            else:
                yield from item_generator(v, lookup_key)
    elif isinstance(json_input, list):
        for item in json_input:
            yield from item_generator(item, lookup_key)

def grab(j, key):
    if isinstance(j, list):
        for item in j:
            yield from grab(item, key)
    elif isinstance(j, dict):
        for k, v in j.items():
            if k == key:
                yield v
            else:
                yield from grab(v, key)

def _parse_select_stmt(catalog, query, sel_json):
    # Get tables (table name -> list of aliases).
    rangevars = list(grab(sel_json, 'RangeVar'))
    tables = set()
    aliases = {}
    for rv in rangevars:
        table = rv['relname']
        tables.add(table)
        if 'alias' in rv:
            alias = rv['alias']['aliasname']
            aliases[alias] = aliases.get(alias, set())
            aliases[alias].add(table)

    wheres = list(grab(sel_json, 'whereClause'))
    columnrefs = list(grab(wheres, 'ColumnRef'))
    targets = []
    for cr in columnrefs:
        fields = cr['fields']
        if len(fields) == 1:
            if 'A_Star' in fields[0]:
                targets.append('*')
            else:
                col = fields[0]['String']['str']
                targets.append(col)
        elif len(fields) == 2:
            alias = fields[0]['String']['str']
            col = fields[1]['String']['str']
            if alias not in aliases:
                # This can happen by naming intermediates.
                targets.append((alias, col))
            else:
                # If there is only one alias, resolve it now.
                candidate_aliases = aliases[alias]
                if len(candidate_aliases) == 1:
                    targets.append((list(candidate_aliases)[0], col))
                else:
                    targets.append((alias, col))
        else:
            raise RuntimeError("What is this? fields: {}, JSON: {}".format(fields, sel_json))

    def mark(table, column):
        if not column.active:
            print(f'Marking {table}.{column.name} active because of {query}.')
        column.active = True

    for target in targets:
        if isinstance(target, str):
            if target == '*':
                for table in tables:
                    for column in catalog.get(table, []):
                        mark(table, column)
            else:
                for table in [c for c in catalog if c in tables]:
                    for column in catalog[table]:
                        if column.name == target:
                            mark(table, column)
        elif isinstance(target, tuple):
            target_table, target_col = target
            for column in catalog.get(target_table, []):
                if column.name == target_col:
                    mark(target_table, column)


def _parse_update_stmt(catalog, query, upd_json):
    pass

def process(catalog, query):
    # Parse the query with pglast.
    query_json = json.loads(pglast.parser.parse_sql_json(query))
    for statement_json in query_json['stmts']:
        statement = statement_json['stmt']
        statement_keys = list(statement.keys())
        assert len(statement_keys) == 1
        statement_type = statement_keys[0]
        # print(statement_type, query)
        if statement_type == 'SelectStmt':
            _parse_select_stmt(catalog, query, statement[statement_type])
        elif statement_type == 'UpdateStmt':
            _parse_update_stmt(catalog, query, statement[statement_type])
        else:
            raise RuntimeError("Unknown statement type {}, query: {}.".format(statement_type, query))

def main():
    catalog = get_catalog()
    pp = Preprocessor(parquet_path='out.parquet.gzip')
    sqls = set(pp.get_grouped_dataframe_params().index.get_level_values(0))
    for i, sql in enumerate(sqls):
        process(catalog, sql)
        # print(i, sql)
    # pprint(catalog)

    with open('./actions.sql', "w") as f:
        for table_name in catalog:
            active_cols = [col.name for col in catalog[table_name] if col.active]

            if active_cols == []:
                continue

            permutations = (
                (table_name, permutation)
                for num_cols in range(1, len(active_cols) + 1)
                for permutation in itertools.permutations(active_cols, num_cols)
            )
            for table, permutation in permutations:
                cols = ",".join(permutation)
                cols_name = "_".join(permutation) + "_key"
                index_name = f"action_{table}_{cols_name}"
                sql = f"create index if not exists {index_name} on {table} ({cols});"
                print(sql, file=f)

if __name__ == '__main__':
    main()