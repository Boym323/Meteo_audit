import unittest
from meteo_audit.db import ReadOnlyQueryError, query

class QueryGuardTests(unittest.TestCase):
    def test_write_and_file_side_effects_rejected(self):
        statements = (
            'UPDATE archive SET rain=0', 'DELETE FROM archive',
            'INSERT INTO t VALUES (1)', 'DROP TABLE archive',
            "SELECT * FROM t INTO OUTFILE '/tmp/x'", 'SELECT * FROM t FOR UPDATE',
        )
        for statement in statements:
            with self.subTest(statement=statement), self.assertRaises(ReadOnlyQueryError):
                query(statement, env_file='/does/not/exist')

    def test_multiple_statements_rejected(self):
        with self.assertRaises(ReadOnlyQueryError):
            query('SELECT 1; SELECT 2', env_file='/does/not/exist')

if __name__ == '__main__':
    unittest.main()
