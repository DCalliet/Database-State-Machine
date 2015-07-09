from db_commands import Help, SaveDB, LoadDB, ListDB, StashDB

def get_command(args):
    if args['subcommand'] == 'help':
        return Help(args['options'])
    elif args['subcommand'] == 'stash_db':
        return StashDB(args['options'])
    elif args['subcommand'] == 'save_db':
        return SaveDB(args['options'])
    elif args['subcommand'] == 'load_db':
        return LoadDB(args['options'])
    elif args['subcommand'] == 'listall':
        return ListDB(args['options'])
    else:
        print args['subcommand'] + " is not implemented."
        return False