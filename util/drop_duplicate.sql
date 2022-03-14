-- Drop any indexes which are duplicate definitions.
SELECT format(
               'DROP INDEX %I;',
               unnest(array_agg(indexrelid::regclass))
           ) as "DROP_COMMANDS"
-- https://www.postgresql.org/docs/14/catalog-pg-index.html
FROM pg_index
-- This is the source of the magic.
-- Group by indrelid (table) and indkey (ordered indexed columns).
GROUP BY indrelid, indkey
-- Select indexes which appear multiple times.
HAVING COUNT(*) > 1
-- Keep the first index.
OFFSET 1
;