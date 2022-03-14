-- Drop any indexes which were unused since the last pg_stat_reset().
SELECT format(
               'DROP INDEX %I;',
               index_name
           ) as "DROP_COMMANDS"
FROM (
         -- Adapted from: https://www.cybertec-postgresql.com/en/get-rid-of-your-unused-indexes/
         SELECT s.indexrelname                 AS index_name,
                pg_relation_size(s.indexrelid) AS index_size
         FROM pg_catalog.pg_stat_user_indexes s
                  JOIN pg_catalog.pg_index i
                       ON s.indexrelid = i.indexrelid
         WHERE
           -- No scan activity since last pg_stat_reset().
             s.idx_scan = 0
           -- No indexed columns are expressions.
           AND 0 <> ALL (i.indkey)
           -- Not enforcing unique constraints.
           AND NOT i.indisunique
           -- Not enforcing constraints in general.
           AND NOT EXISTS
             (
                 SELECT 1
                 FROM pg_catalog.pg_constraint c
                 WHERE c.conindid = s.indexrelid
             )
           -- Not a previously used index.
           -- We track previously used indexes by writing a COMMENT.
           AND (
             -- Check the COMMENT on the index.
             -- If it is NULL, no problem, we can drop it.
             -- If it is our sentinel value, don't drop it.
                 obj_description(s.indexrelid, 'pg_class') IS NULL
                 OR obj_description(s.indexrelid, 'pg_class') <> 'terrier'
             )
           -- Order by index size.
         ORDER BY pg_relation_size(s.indexrelid) DESC
     ) AS cybertec;
\gexec