import os
import re
from collections import defaultdict
import delphin.mrs

##############################################################################
### Global variables

_relations_filename = 'relations'
_field_delimeter = '@'

##############################################################################
### Non-class (i.e. static) functions

def get_relations(profile_directory, relations_filename=_relations_filename):
    """
    Parse the relations file and return a dictionary describing the database
    structure.

    @param profile_directory: The directory where the relations file exists.
    @param relations_filename: The filename containing the database relations.
                               Defaults to 'relations'.
    """

    relations = defaultdict(list)
    relations_table_re = re.compile(r'^(\w.+):$')
    f = open(os.path.join(profile_directory, relations_filename))
    current_table = None
    for line in f:
        table_match = relations_table_re.search(line)
        if table_match is not None:
            current_table = table_match.groups()[0]
        elif len(line.strip()) > 0 and current_table is not None:
            fields = line.split()
            relations[current_table].append(fields[0])
            #TODO: Add data type, key, partial key, comment? etc.
            #TODO: Import db to proper db (sqlite, etc)
    return relations


##############################################################################
### Profile classes

class TsdbTable:
    """
    A class that provides methods for iterating through rows in a
    Tsdb profile table.
    """

    def __init__(self, profile, table_name):
        """
        @param profile: The TsdbProfile this table belongs to.
        @param table_name: The filename of the table.
        """
        self.name = table_name
        self.profile = profile

    def rows(self):
        """
        Iterate through the rows in the Tsdb table.
        """
        f = open(os.path.join(self.profile.root, self.name))
        for line in f:
            #line = unicode(line, 'utf-8')
            yield dict(zip(self.profile.relations[self.name],
                           line.strip().split(_field_delimeter)))
        f.close()

class TsdbProfile:

    def __init__(self, root_directory):
        """
        Given the directory of a [incr TSDB()] profile, analyze the
        database structure and prepare for reading.

        @param root_directory: The directory where the profile files are
                               stored.
        """

        self.root = root_directory
        self.relations = get_relations(self.root)

    def get_table(self, table_name):
        """
        For a given table name, use the information read in the
        relations file to create and return a TsdbTable object.
        """

        return TsdbTable(self, table_name)
