import re

class Derivation(object):
    """
    A class for reading, writing, and storing derivation tree objects.

    @author: T.J. Trimble
    """

    ace_tree_compile = re.compile(r"#T\[(?P<EDGE_ID>\d+) (?P<LABEL>\"?\w+\"?) (?P<TOKEN>\"\w+\"|nil) (?P<CHART_ID>\d+) (?P<RULE_NAME>\w+)\W*(?P<CHILDREN>#T\[.*?\])*\W*\]")
    ace_children = re.compile(r"#T\[.*?\]")


    def __init__(self, representation):
        """
        For now, assume ACE output
        """
        self.read_ACE(representation)

    # Interface specific methods
    #  Maybe move these to their respective interface classes?
    def read_ACE(self, representation):
        # '#T[EDGE_ID "LABEL" ("TOKEN"|nil) CHART_ID RULE_NAME [#T[]]]'
        error = ValueError("Derivation Tree is malformed: {}".format(representation))
        result = Derivation.ace_tree_compile.match(representation)
        # print("\n")
        # print(representation)
        # print(result)
        # print(result.groups())
        if not result:
            raise error
        try:
            self.edge_ID = result.group('EDGE_ID')
            self.label = result.group('LABEL').strip('"')
            self.token = result.group('TOKEN').strip('"') if result.group('TOKEN') != "nil" else None
            self.chart_ID = result.group('CHART_ID')
            self.rule_name = result.group('RULE_NAME')
            # Read in children
            children = result.group('CHILDREN') or "" # defaults
            children = Derivation.ace_children.findall(children)
            #print(children)
            if children:
                self.children = [Derivation(child) for child in children]
            else:
                self.children = []
            #print("\n")
        except IndexError:
            raise error

    # Core methods
    def __eq__(self, other):
        """
        Two trees are equal if their labels, tokens, rule names, and 
        structures are the same. Edge IDs and chart IDs are irrelevant.
        """
        # Check attributes
        if not isinstance(other, Derivation):
            return False
        if self.label != other.label:
            return False
        if self.token != other.token:
            return False
        if self.rule_name != other.rule_name:
            return False
        ## Check children
        if len(self.children) != len(other.children):
            return False
        for i in range(len(self.children)):
            if self.children[i] != other.children[i]:
                return False
        # Return true if they're the same!
        return True

    def __str__(self):
        # TODO: this
        return self.get_HTML()

    # HTML Methods
    def get_HTML(self, title_text=True):
        """
        Returns HTML representation of tree in the following format:
            <div id=CHART_ID title="CHART_ID: RULE_NAME"><p>LABEL</p>(<p>TOKEN</p>)?</div>
        
        By default, this method returns HTML styled with the HTML's title
        attribute set to the rule used and the parse chart ID. Pass
        title_text=False to disable this.
        """
        result = "<div id={CHART_ID}{TITLE}><p>{LABEL}</p>{TOKEN}{CHILDREN}</div>"
        # Add token if applicable
        values = {
            "CHART_ID": self.chart_ID,
            "RULE_NAME": self.rule_name,
            "LABEL": self.label,
            "TOKEN": "<p>{}</p>".format(self.token) if self.token else "",
            "TITLE": " title=\"{}: {}\"".format(self.chart_ID, self.rule_name) if title_text else "",
            "CHILDREN": "".join(child.get_HTML(title_text=title_text) for child in self.children)
        }
        # Return result
        return result.format(**values)

    # Pickle Methods
    def read(self):
        pass

    def reads(self):
        pass

    def dump(self):
        pass

    def dumps(self):
        pass
