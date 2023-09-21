import sqlite3
import logging


class watch_list_db():
    '''watch list database controller

    Parameters
    ----------
    dbname : string
        sqlite3 db file path
    logger : logging.Logger
        logger

    Result
    ------
    watch_list_db : Object

    Example
    -------
    >>> import datetime
    >>> t = datetime.datetime.now()
    >>> watch_list = watch_list_db(f'test_{t.timestamp()}.db')
    >>> watch_list.add_watch_list('TESTID1', 'TESTNAME1')
    >>> watch_list.add_watch_list('TESTID2', 'TESTNAME2')
    >>> watch_list.add_watch_list('TESTID3', 'TESTNAME3')
    >>> watch_list.rm_watch_list('TESTID2')
    >>> chlist = watch_list.get_watch_list()
    >>> chlist[0]
    ('TESTID1', 'TESTNAME1')
    >>> chlist[1]
    ('TESTID3', 'TESTNAME3')
    '''

    TBL_NAME = 'watch_list'

    def __init__(self, dbname, logger=None):
        self._dbname = dbname
        self._db = None
        self._create_sql = f'''CREATE TABLE IF NOT EXISTS {self.TBL_NAME} (
            _ch_id      TEXT,     -- Channel ID on slack
            _ch_name    TEXT,     -- CHannel Name on slack
            PRIMARY KEY (_ch_id)
        );
        '''
        self._insert_sql = f'INSERT INTO {self.TBL_NAME} VALUES (?, ?)'
        self._remove_sql = f"DELETE FROM {self.TBL_NAME} WHERE _ch_id='{{0}}'"
        self._select_sql = f'SELECT * FROM {self.TBL_NAME}'
        if logger is None:
            self._logger = logging.getLogger(__name__)
        else:
            self._logger = logger

    def _open_db(self):
        self._logger.debug('open_db called')

        if self._db is None:
            self._logger.info('open db')
            self._db = sqlite3.connect(self._dbname)

    def _make_table(self):
        self._logger.debug('make_table called')

        self._open_db()

        self._logger.info('cursor open')
        cur = self._db.cursor()
        cur.execute(self._create_sql)

        self._logger.info('commit and cursor close')
        self._db.commit()
        cur.close()

    def _insert_value(self, ch_id, ch_name):
        self._logger.debug('insert_value called')

        self._make_table()

        self._logger.info('cursor open')
        cur = self._db.cursor()
        cur.execute(self._insert_sql, (ch_id, ch_name,))

        self._logger.info('commit and cursor close')
        self._db.commit()
        cur.close()

    def _remove_value(self, ch_id):
        self._logger.debug('remove_value called')

        self._open_db()

        self._logger.info('cursor open')
        cur = self._db.cursor()
        cur.execute(self._remove_sql.format(ch_id))

        self._logger.info('commit and cursor close')
        self._db.commit()
        cur.close()

    def _select_value(self):
        self._logger.debug('select_value called')

        self._make_table()

        self._logger.info('cursor open')
        cur = self._db.cursor()
        cur.execute(self._select_sql)
        chlist = cur.fetchall()

        self._logger.info('cursor close')
        cur.close()

        return chlist

    def add_watch_list(self, ch_id, ch_name=""):
        self._logger.debug('add_watch_list called')

        self._insert_value(ch_id, ch_name)

    def rm_watch_list(self, ch_id):
        self._logger.debug('rm_watch_list called')

        self._remove_value(ch_id)

    def get_watch_list(self):
        self._logger.debug('get_watch_list called')

        return self._select_value()

    def close(self):
        self._logger.debug('close called')

        if self._db is not None:
            self._logger.info('close database')
            self._db.close()


if __name__ == '__main__':
    import doctest
    doctest.testmod()
