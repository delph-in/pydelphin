import os
import re
from collections import defaultdict

##############################################################################
### Global variables

_relations_filename = 'relations'
_field_delimiter = '@'

##############################################################################
### Non-class (i.e. static) functions

def get_relations(path):
    """
    Parse the relations file and return a dictionary describing the database
    structure.

    @param profile_directory: The directory where the relations file exists.
    @param relations_filename: The filename containing the database relations.
                               Defaults to 'relations'.
    """

    relations = defaultdict(list)
    relations_table_re = re.compile(r'^(\w.+):$')
    f = open(path)
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
        tbl_filename = os.path.join(self.profile.root, self.name)
        # Don't crash if table doesn't exist, just yield nothing
        if not os.path.exists(tbl_filename):
            raise StopIteration
        f = open(tbl_filename)
        for line in f:
            #line = unicode(line, 'utf-8')
            yield dict(zip(self.profile.relations[self.name],
                           line.strip().split(_field_delimiter)))
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
        self.relations = get_relations(os.path.join(self.root,
                                                    _relations_filename))

    def get_table(self, table_name):
        """
        For a given table name, use the information read in the
        relations file to create and return a TsdbTable object.
        """

        return TsdbTable(self, table_name)

    def write_profile(self, profile_directory, relations_filename=None):
        """
        Using self.relations as a schema, write the profile data out to
        the specified profile directory.

        @param profile_directory: The directory where the profile will
            be written.
        @param relations_file: If specified, provides an alternative
            relations file for the profile to be written.
        """
        import shutil
        if relations_filename:
            relations = get_relations(relations_filename)
        else:
            relations = self.relations
        shutil.copyfile(relations_filename, os.path.join(profile_directory,
                                                         _relations_filename))
        for tbl_name in relations.keys():
            # don't create new empty files if they didn't already exist
            # (likely was a skeleton rather than a profile)
            if not os.path.exists(os.path.join(self.root, tbl_name)):
                continue
            tbl = open(os.path.join(profile_directory, tbl_name), 'w')
            for row in self.get_table(tbl_name).rows():
                print >>tbl, _field_delimiter.join(
                    row.get(f, '') for f in relations[tbl_name])
            tbl.close()
