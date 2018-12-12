import os
import tornado.web
import tornado.locks
from tornado.ioloop import IOLoop
from tornado.options import define, options
from sqlalchemy.orm import sessionmaker
from aiopg.sa import create_engine
import psycopg2

from utils import load_json_data, find_resource, write_json_data
from handlers import (
    MainHandler,
    Companies,
    Company,
    Addresses,
    Address,
    PeopleHandler,
    Files,
    Departments,
    Contacts,
    Employees,
    Spectrum,
    TypeApproval,
    Numbering,
    Spectrum,
    Postal,
    Telecom,
    Broadcasting)


HANDLERS = [
        (r"/", MainHandler),
        ("/companies", Companies),
        (r"/companies/([^/]+)?", Company),
        ("/addresses", Addresses),
        ("/addresses/([^/]+)?", Address),
        ("/people/([^/]+)?", PeopleHandler),
        ("/files/([^/]+)?", Files),
        ("/departments/([^/]+)?", Departments),
        ("/contacts/([^/]+)?", Contacts),
        ("/employees/([^/]+)?", Employees),
        ("/spectrum/([^/]+)?", Spectrum),
        ("/typeapproval/([^/]+)?", TypeApproval),
        ("/numbering/([^/]+)?", Numbering),
        ("/broadcasting/([^/]+)?", Broadcasting),
        ("/postal/([^/]+)?", Postal),
        ("/telecom/([^/]+)?", Telecom)
    ]
datastore = {}


class Application(tornado.web.Application):
    def __init__(self, db, engine):
        self.db = db
        Session = sessionmaker(db)
        Session.configure(bind=engine)
        self.session = Session()
        # Define constant with handlers for different routes
        handlers = HANDLERS
        settings = dict(
            xsrf_cookies=True,
            cookie_secret="__TODO:_GENERATE_YOUR_OWN_RANDOM_VALUE_HERE__",
            debug=True,
        )
        super(Application, self).__init__(handlers, **settings)


async def populate_data(app):
    for handler in HANDLERS:
        name = handler[0].split("/")[1]
        item = name
        if not item.strip():
            continue
        item = load_json_data(
            os.path.join(os.path.dirname(__file__), "mock_data"),
            name)
        datastore[name] = item


async def maybe_create_tables(conn):
    """ Generate tables from schemas """
    try:
        await conn.execute("DROP TABLE IF EXISTS people")
        await conn.execute(
            """CREATE TABLE people (
                id serial PRIMARY KEY,
                first_name varchar(255),
                last_name varchar(255),)""")
    except psycopg2.ProgrammingError:
        pass


def define_args():
    """ Define arguments for application use """
    define("port", default=8888, help="run on the given port")
    define("db_host", default="127.0.0.1", help="database host")
    define("db_port", default=5432, help="database port")
    define("db_database", default="ims", help="ims database")
    define("db_user", default="root", help="database user")
    define("db_password", default="", help="database password")
    tornado.options.parse_command_line(final=False)
    file_name = "{}/server.conf".format(os.path.dirname(__file__))
    tornado.options.parse_config_file(file_name)


async def main():
    define_args()
    engine = await create_engine(
        host=options.db_host,
        port=options.db_port,
        user=options.db_user,
        password=options.db_password,
        database=options.db_database,
    )

    async with engine.acquire() as conn:
        # await maybe_create_tables(conn)
        app = Application(conn, engine)
        app.listen(options.port)

        shutdown_event = tornado.locks.Event()
        await shutdown_event.wait()

if __name__ == "__main__":
    tornado.ioloop.IOLoop.current().run_sync(main)
