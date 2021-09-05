# This script allows easy access to Galaxy's data table database layer via the
# Galaxy models. For example:
# %  python -i scripts/db_data_tables_shell.py data_tables

import datetime
import decimal
import os.path
import sys

# Setup DB scripting environment
from sqlalchemy import *  # noqa
from sqlalchemy.orm import *  # noqa
from sqlalchemy.exc import *  # noqa
from sqlalchemy.sql import label  # noqa

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'lib')))

from galaxy.model.data_tables import *  # noqa
from galaxy.model.data_tables.mapping import init
from galaxy.model.orm.scripts import get_config

db_url = get_config(sys.argv)['db_url']
sa_session = init(db_url).context


# Helper function for debugging sqlalchemy queries...
# http://stackoverflow.com/questions/5631078/sqlalchemy-print-the-actual-query
def printquery(statement, bind=None):
    """
    Print a query, with values filled in
    for debugging purposes *only*
    for security, you should always separate queries from their values
    please also note that this function is quite slow
    """
    import sqlalchemy.orm
    if isinstance(statement, sqlalchemy.orm.Query):
        if bind is None:
            bind = statement.session.get_bind()
        statement = statement.statement
    elif bind is None:
        bind = statement.bind

    dialect = bind.dialect
    compiler = statement._compiler(dialect)

    class LiteralCompiler(compiler.__class__):
        def visit_bindparam(
                self, bindparam, within_columns_clause=False,
                literal_binds=False, **kwargs
        ):
            return super().render_literal_bindparam(
                bindparam,
                within_columns_clause=within_columns_clause,
                literal_binds=literal_binds,
                **kwargs
            )

        def render_literal_value(self, value, type_):
            """Render the value of a bind parameter as a quoted literal.

            This is used for statement sections that do not accept bind paramters
            on the target driver/database.

            This should be implemented by subclasses using the quoting services
            of the DBAPI.

            """
            if isinstance(value, str):
                value = value.replace("'", "''")
                return "'%s'" % value
            elif value is None:
                return "NULL"
            elif isinstance(value, (float, int)):
                return repr(value)
            elif isinstance(value, decimal.Decimal):
                return str(value)
            elif isinstance(value, datetime.datetime):
                return "TO_DATE('%s','YYYY-MM-DD HH24:MI:SS')" % value.strftime("%Y-%m-%d %H:%M:%S")

            else:
                raise NotImplementedError(
                    "Don't know how to literal-quote value %r" % value
                )

    compiler = LiteralCompiler(dialect, statement)
    print(compiler.process(statement))
