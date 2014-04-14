class SemI(object):
    def __init__(self, vpm=None):
        self._vpm = vpm

    def map_properties_left_to_right(self, props):
        return self._vpm.map_lr(props)

    def map_properties_right_to_left(self, props):
        return self._vpm.map_rl(props)


class Vpm(object):
    # NOTE: why not a VpmMap class that tests for matches then applies the
    #       mapping? It would make things cleaner, but consider the
    #       computational efficiency costs

    def __init__(self):

        # note, we have to iterate over all mappings in order, so consider
        # using a list instead of, e.g., an OrderedDict
        # self._mappings = {(LEFTPROP,RIGHTPROP):[(left,op,right),...],...}
        #   A mapping key of (None, None) is reserved for variable type
        #   mappings, and others are for variable property mappings
        self._mappings = []

    def add_mapping(self, left, right):
        pass

    def map_properties(self, properties, reverse=False):
        """
        Return a dictionary of properties and their values after the
        applicable VPM rules have applied.
        @param properties: A dictionary of {property:value}
        @param reverse: If True, the rules will map variable properties from
                        right-to-left instead of left-to-right.
        @returns: A dictionary of {property:value}
        """
        frm = lambda x: x[-1] if reverse else x[0]
        to = lambda x: x[0] if reverse else x[-1]
        valid_ops = ('<' if reverse else '>', '=')
        op_match = lambda x: to(x[1]) in valid_ops
        match = lambda x: self.map_match(properties, x, frm, to, op_match)
        return dict((prop, val)
                    for (pm, vmlist) in self._mappings
                    for prop, val in self.find_map(properties, pm, vm,
                                                   frm, to, match))

    def find_map(self, properties, pm, vm, frm, to, match):
        return [next(zip(to(pm), to(vm)) for vm in filter(match, vmlist))]

    def map_match(self, properties, valmap, frm, to, op_match):
        """
        Return True if the "from" side of the valmap matches the properties.
        A match is obtained if properties match a mapping given the operator,
        the mapping specifies * and the property is non-null
        TODO: what about conditions of the variable, e.g. [e]
        """
        pass
        # apply_op = lambda x, y: x == y if
        # check_op = lambda op, vm: properties.
        # return all(check_op(properties[p], op, v)
        #           for (p, v) in zip(to(
        # match = (zip(propmap[to_idx], valmap[to_idx])
        #         for valmap in filter(op_match, valmaplist)
        #         if match(properties, valmap[1], valmap[from_idx])).next(
        # match = []
        # for valmap in filter(op_match, valmaplist):

        #    for (prop, val) in zip(propmap[from_idx], valmap[from_idx]):
        #        if properties[prop] == val or\
        #           val == '*' and properties.get(prop) is not None or\
        #           val == '!' and properties.get(prop) is None:

        #    # break after finding first
        # return match
