import sys, os
from db_init import get_command

class DBUtility(object):
    def __init__(self, argv=None):
        self.argv = argv or sys.argv[:]
        self.prog_name = os.path.basename(self.argv[0])

    def execute(self):
        args = {}
        try:
            subcommand = self.argv[1]
        except IndexError:
            subcommand = 'help'

        try:
            options = self.argv[2:]
        except IndexError:
            options = {}

        args.update({"subcommand": subcommand, "options": options})
        command = get_command(args)

        if command:
            command.run()
        else:
            pass
