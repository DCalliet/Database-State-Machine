# Database-State-Machine
======================


This tool is for individuals who are constantly going back and forth between versions
of their database, and thus have to run code to re-migrate it, apply the migrations, and
eventually wait as some script repopulates their database with data.

**Intended for local database use**

Inspired by the concept of git stash, you can stash away a current state of your database.
This allows you to switch branches, do whatever you want to your database, and easily restore it to any saved state!

##Setup
=======

In the settings.py file:

Set *'db.NAME'* to the name of your working database *(Please make sure it exists!)* \n
Set *'db.USER'* to an owner of your working database *(We must have full permissions!)* \n

If the default *'db.STATE_TABLE_NAME'* and *'db.TEMP_DATABASE_NAME'* will conflict with
an existing table or database (respectively) feel free to change those names! \n

##Usage
=======

- **db_management.py help**
- **db_management.py save_db <state name>**  gives your working directory a state to be saved as when swapped for a load.
- **db_management.py stash_db <state name>**  stashes a copy of your database with a state we use to identify it
- **db_management.py load_db <state name>** finds the db state, and loads it as your working db. Your current one gets stashed away.


##Future Improvements
=====================
- **load_db**  allow user to drop instead of being forced to stash the current working db
- **delete_state <state name> (default:all)** - allow user to delete a single or all state db's *(can remove state from working but not delete it)*

