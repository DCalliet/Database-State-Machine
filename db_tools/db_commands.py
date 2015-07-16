import abc, sys, os
import re
import datetime
import psycopg2
from settings import db, bcolors

class CommandBase(object):
    __metaclass__ = abc.ABCMeta

    def run(self):
        if self.options == False:
            print "ArgumentError: " + self.error
            return False

        if self.options[0] == "--help":
            self.help()
        else:
            self.execute(self.options)

    @abc.abstractmethod
    def legal_args(self, options):
        pass

    @abc.abstractmethod
    def help(self):
        pass
    
    @abc.abstractmethod    
    def execute(self, options):
        pass

class Help(CommandBase):
    
    subcommand = 'help'
    helptext = '''
{header}Database State Machine:{end}\n
{underline}This program has the following commands:{end}
{blue}- help\n- save_db <status name>\n- stash_db <status name>\n- load_db <status name>\n- listall\n{end}

Use '--help' as a first option on any command to get a description.

            '''.format(blue=bcolors.OKBLUE, bold=bcolors.BOLD, header=bcolors.HEADER, underline=bcolors.UNDERLINE, end=bcolors.ENDC)

    def __init__(self, options=[]):
        self.options = self.legal_args(options)

    def legal_args(self, options):
        return [None]

    def help(self, options):
        print self.helptext

    def execute(self, options):
        self.help(options)

class SaveDB(CommandBase):

    subcommand = 'save_db'
    helptext = '{bold}Description:{end}\nSaves our state object to the database you are currently working on.'.format(bold=bcolors.BOLD, end=bcolors.ENDC)
    argumentstext = "python db_management.py save_db <status name>"

    def __init__(self, options=[]):
        self.options = self.legal_args(options)

    def legal_args(self, options=[]):
        if len(options) == 0:
            self.error = "{fail}Too few arguments{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        elif len(options) > 1:
            self.error = "{fail}Too many arguments{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        elif options[0] == "--help":
            return options
        elif not re.match(r"^[a-zA-Z_]*$", options[0]):
            self.error = "{fail}Illegal database name{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        else:
            return options

    def help(self):
        print self.helptext

    def execute(self, options):
        if options[0] == '--help':
            print self.helptext
            return False
        con = None
        new_state = options[0]
        #Insert new_state in table so it can be restored at a later point
        try:
            con = psycopg2.connect(database=db.NAME, user=db.USER)
            cursor = con.cursor()
            
            query = '''
                SELECT datname FROM pg_database WHERE datistemplate = false;
            '''
            cursor.execute(query)
            rows = [result[0] for result in cursor.fetchall()]
            
            while ('{base}_{state}'.format(base=db.NAME, state=new_state) in rows):
                print "A database already has this status, create with a timestamp? (Y/N)"
                if sys.stdin.readline().strip().lower() == 'y':
                    time = datetime.datetime.now().strftime('%b%d_%H_%M')
                    new_state += time
                else:
                    print "Would you mind providing us a status to use?"
                    new_state = sys.stdin.readline().strip()

            query = '''
                CREATE TABLE IF NOT EXISTS {table} (name char(255) PRIMARY KEY);
                DELETE FROM {table};
                INSERT INTO {table} VALUES ('{state}');
            '''.format(table=db.STATE_TABLE_NAME, state=new_state)
            cursor.execute(query)
            con.commit()
        except psycopg2.DatabaseError, e:
            print "Error: {}".format(e)
            con.close()
            return False

        finally:
            if con:
                con.close()
        
        print "SAVED"

class StashDB(CommandBase):

    subcommand = 'stash_db'
    helptext = '{bold}Description:{end}\nThis command creates a duplicate of your database'.format(bold=bcolors.BOLD, end=bcolors.ENDC)
    argumentstext = "python db_management.py stash_db <status name>"

    def __init__(self, options=[]):
        self.options = self.legal_args(options)

    def legal_args(self, options=[]):
        if len(options) == 0:
            self.error = "{fail}Too few arguments{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        elif len(options) > 1:
            self.error = "{fail}Too many arguments{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        elif options[0] == '--help':
            return options
        elif not re.match(r"^[a-zA-Z_]*$", options[0]):
            self.error = "{fail}Illegal database name{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        else:
            return options

    def help(self):
        print self.helptext

    def execute(self, options):
        if options[0] == '--help':
            print self.helptext
            return False
        con = None
        new_state = "{base}_{state}".format(state=options[0], base=db.NAME)
        # Create  duplicate db, returns if we fail.
        error = os.system("createdb -O {user} -T {base} {state}".format(user=db.USER, base=db.NAME, state=new_state))
        if error == 256:
            print "A database already has this status, create with timestamp? (Y/N)"
            if sys.stdin.readline().strip().lower() == 'y':
                time = datetime.datetime.now().strftime('%b%d_%H_%M')
                new_state += time
                error = os.system("createdb -O {user} -T {base} {state}".format(user=db.USER, base=db.NAME, state=new_state))
                if error == 0:
                    print "CREATED"
            else:
                return False
        elif error == 0:
            print "CREATED"

        #Insert new_state in table so it can be restored at a later point
        try:
            con = psycopg2.connect(database=new_state, user=db.USER)
            cursor = con.cursor()
            query = '''
                CREATE TABLE IF NOT EXISTS {table} (name char(255) PRIMARY KEY);
                DELETE FROM {table};
                INSERT INTO {table} VALUES ('{state}');
            '''.format(table=db.STATE_TABLE_NAME, state=options[0])
            cursor.execute(query)
            con.commit()
        
        except psycopg2.DatabaseError, e:
            print "Error: {}".format(e)
            con.close()
            os.system("dropdb {state}".format(state=new_state))
            return False

        finally:

            if con:
                con.close()


class LoadDB(CommandBase):

    subcommand = 'load_db'
    helptext = '{bold}Description:{end}\nLoads a stashed database'.format(bold=bcolors.BOLD, end=bcolors.ENDC)
    argumentstext = "python db_management.py load_db <status name>"

    def __init__(self, options=[]):
        self.options = self.legal_args(options)

    def legal_args(self, options=[]):
        if len(options) == 0:
            self.error = "{fail}Too few arguments{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        elif len(options) > 1:
            self.error = "{fail}Too many arguments{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        elif options[0] == "--help":
            return options
        elif not re.match(r"^[a-zA-Z_]*$", options[0]):
            self.error = "{fail}Illegal database name{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            return False
        else:
            return options

    def help(self):
        print self.helptext

    @staticmethod
    def overwrite(con, cursor, target):
        con = psycopg2.connect(database='{tmp_db}'.format(tmp_db=db.TEMP_DATABASE_NAME), user=db.USER)
        cursor = con.cursor()
        query = '''
        DROP DATABASE {base};
        ALTER DATABASE {target} RENAME TO {base};
        '''.format(base=db.NAME, target=target)
        try:
            cursor.execute(query)
            con.commit()
        except psycopg2.ProgrammingError:
            print "Unexpected Error"
            return False
        finally:
            if con:
                con.close()

    @staticmethod
    def switch(con, cursor, target, rows, new_state=None):
        need_table = False
        if new_state is None:
            need_table = True
            print "Would you mind providing us a status to use?"
            new_state = sys.stdin.readline().strip()
        while '{base}_{state}'.format(base=db.NAME, state=new_state) in rows:
            print "A database already has this status, create with a timestamp? (Y/N)"
            if sys.stdin.readline().strip().lower() == 'y':
                time = datetime.datetime.now().strftime('%b%d_%H_%M')
                new_state += time
            else:
                print "Would you mind providing us a status to use?"
                new_state = sys.stdin.readline().strip()
        if need_table:
            try:
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS {table} (name char(255) PRIMARY KEY);
                DELETE FROM {table};
                INSERT INTO {table} VALUES ('{state}');
                '''.format(table=db.STATE_TABLE_NAME))
                con.commit()
            except psycopg2.ProgrammingError:
                con.rollback()

        con.close()
        con = psycopg2.connect(database='{tmp_db}'.format(tmp_db=db.TEMP_DATABASE_NAME), user=db.USER)
        cursor = con.cursor()
        query = '''
        ALTER DATABASE {base} RENAME TO {base}_{state};
        ALTER DATABASE {target} RENAME TO {base};
        '''.format(base=db.NAME, state=new_state, target=target)
        try:
            cursor.execute(query)
            con.commit()
        except psycopg2.ProgrammingError:
            print "Unexpected Error"
            return False
        finally:
            if con:
                con.close()

    def execute(self, options):
        if options[0] == '--help':
            print self.helptext
            return False
        # temp db
        os.system("dropdb {tmp_db}".format(tmp_db=db.TEMP_DATABASE_NAME))
        os.system("createdb {tmp_db} -O {user} ".format(tmp_db=db.TEMP_DATABASE_NAME, user=db.USER))

        target = '{base}_{target}'.format(base=db.NAME, target=options[0])
        con = psycopg2.connect(database=db.NAME, user=db.USER)
        cursor = con.cursor()
        query = '''
            SELECT datname FROM pg_database WHERE datistemplate = false;
        '''
        cursor.execute(query)
        rows = [result[0] for result in cursor.fetchall()]
        # Ensure we are switching to a valid database status
        if target not in rows:
            print "database status not found"
            return False
        else:
            query = '''
                SELECT name FROM {table};
            '''.format(table=db.STATE_TABLE_NAME)
            new_state = ''
            try:
                cursor.execute(query)
                new_state = cursor.fetchone()[0]
            except psycopg2.ProgrammingError:
                print "This database is not a tracked state, would you like to save it?(Y/N)"
                con.rollback()
                if sys.stdin.readline().strip().lower() == 'y':
                    self.switch(con, cursor, target, rows)
                else:
                    self.overwrite(con, cursor, target)

            self.switch(con, cursor, target, rows, new_state)
        os.system("dropdb {tmp_db}".format(tmp_db=db.TEMP_DATABASE_NAME))

class ListDB(CommandBase):
    subcommand = 'listall'
    helptext = 'This command lists all of your saved states'
    argumentstext = "python db_management.py listall"

    def __init__(self, options=[]):
        self.options = self.legal_args(options)

    def legal_args(self, options=[]):
        return [None]

    def help(self):
        print self.helptext

    def execute(self, options):
        if options[0] == '--help':
            print self.helptext
            return False
        con = psycopg2.connect(database=db.NAME, user=db.USER)
        cursor = con.cursor()
        query = '''
                SELECT name FROM {table};
            '''.format(table=db.STATE_TABLE_NAME)
        print "{underline}Working state{end}".format(underline=bcolors.UNDERLINE, end=bcolors.ENDC)
        try:
            cursor.execute(query)
            a = cursor.fetchone()
            print "{working_state}\n".format(underline=bcolors.UNDERLINE, end=bcolors.ENDC, working_state=a[0].strip())
        except TypeError:
            print "{fail}State not saved{end}\n".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            con.rollback()
        except psycopg2.ProgrammingError:
            print "{fail}State not saved{end}\n".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            con.rollback()
            
        query = '''
            SELECT datname FROM pg_database WHERE datistemplate = false and datname LIKE '{base}%' and datname NOT LIKE '{base}';
        '''.format(base=db.NAME)
        print "{underline}Available states{end}".format(underline=bcolors.UNDERLINE, end=bcolors.ENDC)
        try:
            cursor.execute(query)
            rows = [result[0].replace('topopps_','') for result in cursor.fetchall()]
            output = '\n'.join(rows) if len(rows) > 0 else "{fail}No available states{end}".format(fail=bcolors.FAIL, end=bcolors.ENDC)
            print output
        except psycopg2.ProgrammingError, e:
            print e
            print "Unexpected error"
        finally:
            if con:
                con.close()

class DropDB(CommandBase):
    subcommand = 'drop_db'
    helptext = 'This command removes all database states you specify {blue}(all if left blank){end}'.format(blue=bcolors.OKBLUE, end=bcolors.ENDC)
    argumentstext = "python db_management.py drop_all arg1 arg2 arg3"

    def __init__(self, options=[]):
        self.options = self.legal_args(options)

    def legal_args(self, options=[]):
        if len(options) == 0:
            return [None]
        elif options[0] == '--help':
            return options
        else:
            for el in options:
                if not re.match(r"^[a-zA-Z_]*$",el):
                    self.error = "One or more illegal state names."
                    return False
            return options


    def help(self):
        print self.helptext

    def execute(self, options):
        name = ''
        delete_all = False
        if options[0] is None:
            delete_all = True
        elif options[0] == '--help':
            self.help()
            return False
        con = psycopg2.connect(database=db.NAME, user=db.USER)
        cursor = con.cursor()
        query = '''
            SELECT datname FROM pg_database WHERE datistemplate = false and datname LIKE '{base}%' and datname NOT LIKE '{base}';
        '''.format(base=db.NAME)
        try:
            cursor.execute(query)
            rows = [result[0].strip() for result in cursor.fetchall()]
        except psycopg2.ProgrammingError, e:
            con.rollback()
            print e

        if delete_all:
            print "Are you sure you want to delete all the saved state data? (Y/N)"
            if sys.stdin.readline().strip().lower() != 'y':
                return False

        drop_rows = rows if delete_all else ["topopps_{}".format(state) for state in options if "topopps_{}".format(state) in rows]

        for row in drop_rows:
            os.system("dropdb {db}".format(db=row))
            print "{fail}[DELETED]: {end}{row}".format(fail=bcolors.FAIL, end=bcolors.ENDC, row=row)

        try:
            cursor.execute("SELECT name FROM {table}".format(table=db.STATE_TABLE_NAME))
            name = cursor.fetchone()[0].strip()
            if name in options:
                cursor.execute("DROP TABLE {table}".format(table=db.STATE_TABLE_NAME))
                con.commit()
                print "Dropped tracking from working database"
        except psycopg2.ProgrammingError:
            pass

        if len(drop_rows) == 0 and name not in options:
            print "Nothing to delete."

        con.close()