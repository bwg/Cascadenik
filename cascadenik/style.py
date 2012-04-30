import re
import sys
import os.path
import urlparse
import operator
from itertools import chain, product
from binascii import unhexlify as unhex
from cssutils.tokenize2 import Tokenizer as cssTokenizer

class color:
    def __init__(self, r, g, b):
        self.channels = r, g, b

    def __repr__(self):
        return '#%02x%02x%02x' % self.channels

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return self.channels == other.channels

class color_transparent(color):
    pass

class uri:
    def __init__(self, address):
        self.address = address

    def __repr__(self):
        return str(self.address) #'url("%(address)s")' % self.__dict__

    def __str__(self):
        return repr(self)

class boolean:
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        if self.value:
            return 'true'
        else:
            return 'false'

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return hasattr(other, 'value') and bool(self.value) == bool(other.value)

class numbers:
    def __init__(self, *values):
        self.values = values

    def __repr__(self):
        return ','.join(map(str, self.values))

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        return self.values == other.values

# recognized properties

properties = {
    #--------------- map

    # 
    'map-bgcolor': color_transparent,

    #--------------- polygon symbolizer

    # polygon fill color
    'polygon-fill': color,

    # gamma value affecting level of antialiases of polygon edges
    # 0.0 - 1.0 (default 1.0 - fully antialiased) 
    'polygon-gamma': float,

    # 0.0 - 1.0 (default 1.0)
    'polygon-opacity': float,

    # metawriter support
    'polygon-meta-output': str,

    'polygon-meta-writer': str,

    #--------------- line symbolizer

    # CSS colour (default "black")
    'line-color': color,

    # 0.0 - n (default 1.0)
    'line-width': float,

    # 0.0 - 1.0 (default 1.0)
    'line-opacity': float,

    # miter, round, bevel (default miter)
    'line-join': ('miter', 'round', 'bevel'),

    # round, butt, square (default butt)
    'line-cap': ('butt', 'round', 'square'),

    # d0,d1, ... (default none)
    'line-dasharray': numbers, # Number(s)

    # metawriter support
    'line-meta-output': str,

    'line-meta-writer': str,

    #--------------- line symbolizer for outlines

    # CSS colour (default "black")
    'outline-color': color,

    # 0.0 - n (default 1.0)
    'outline-width': float,

    # 0.0 - 1.0 (default 1.0)
    'outline-opacity': float,

    # miter, round, bevel (default miter)
    'outline-join': ('miter', 'round', 'bevel'),

    # round, butt, square (default butt)
    'outline-cap': ('butt', 'round', 'square'),

    # d0,d1, ... (default none)
    'outline-dasharray': numbers, # Number(s)

    # metawriter support
    'outline-meta-output': str,

    'outline-meta-writer': str,

    #--------------- line symbolizer for inlines

    # CSS colour (default "black")
    'inline-color': color,

    # 0.0 - n (default 1.0)
    'inline-width': float,

    # 0.0 - 1.0 (default 1.0)
    'inline-opacity': float,

    # miter, round, bevel (default miter)
    'inline-join': ('miter', 'round', 'bevel'),

    # round, butt, square (default butt)
    'inline-cap': ('butt', 'round', 'square'),

    # d0,d1, ... (default none)
    'inline-dasharray': numbers, # Number(s)

    # metawriter support
    'inline-meta-output': str,

    'inline-meta-writer': str,

    #--------------- text symbolizer

    'text-anchor-dx':int,
    'text-anchor-dy':int,
    'text-align': ('left','middle','right',),
    'text-vertical-align': ('top','middle','bottom',),
    'text-justify-align': ('left','middle','right',),
    'text-transform': ('uppercase','lowercase',),
    'text-force-odd-labels':boolean,
    # Font name
    'text-face-name': str,

    # Fontset name
    'text-fontset': str,

    # Font size
    'text-size': int,

    # ?
    'text-ratio': None, # ?

    # length before wrapping long names
    'text-wrap-width': int,

    # space between repeated labels
    'text-spacing': int,

    # Horizontal spacing between characters (in pixels).
    'text-character-spacing': int,

    # Vertical spacing between lines of multiline labels (in pixels)
    'text-line-spacing': int,

    # allow labels to be moved from their point by some distance
    'text-label-position-tolerance': int,

    # Maximum angle (in degrees) between two consecutive characters in a label allowed (to stop placing labels around sharp corners)
    'text-max-char-angle-delta': int,

    # Color of the fill ie #FFFFFF
    'text-fill': color,

    # Color of the halo
    'text-halo-fill': color,

    # Radius of the halo in whole pixels, fractional pixels are not accepted
    'text-halo-radius': int,

    # displace label by fixed amount on either axis.
    'text-dx': int,
    'text-dy': int,

    # Boolean to avoid labeling near intersection edges.
    'text-avoid-edges': boolean,

    # Minimum distance between repeated labels such as street names or shield symbols
    'text-min-distance': int,

    # Allow labels to overlap other labels
    'text-allow-overlap': boolean,

    # "line" to label along lines instead of by point
    'text-placement': ('point', 'line'),

    # metawriter support
    'text-meta-output': str,

    'text-meta-writer': str,

    #--------------- point symbolizer

    # path to image file
    'point-file': uri, # none

    # px (default 4), generally omit this and let PIL handle it
    'point-width': int,
    'point-height': int,

    # image type: png or tiff, omitted thanks to PIL
    'point-type': None,

    # true/false
    'point-allow-overlap': boolean,

    # metawriter support
    'point-meta-output': str,

    'point-meta-writer': str,

    #--------------- raster symbolizer

    # raster transparency
    # 0.0 - 1.0 (default 1.0)
    'raster-opacity': float,
    
    # Compositing/Merging effects with image below raster level
    # default normal
    'raster-mode': ('normal','grain_merge', 'grain_merge2',
                    'multiply', 'multiply2', 'divide', 'divide2',
                    'screen', 'hard_light'),
    
    # resampling method
    'raster-scaling': ('fast', 'bilinear', 'bilinear8',),
        
    #--------------- polygon pattern symbolizer

    # path to image file (default none)
    'polygon-pattern-file': uri,

    # px (default 4), generally omit this and let PIL handle it
    'polygon-pattern-width': int,
    'polygon-pattern-height': int,

    # image type: png or tiff, omitted thanks to PIL
    'polygon-pattern-type': None,

    # metawriter support
    'polygon-pattern-meta-output': str,

    'polygon-pattern-meta-writer': str,

    #--------------- line pattern symbolizer

    # path to image file (default none)
    'line-pattern-file': uri,

    # px (default 4), generally omit this and let PIL handle it
    'line-pattern-width': int,
    'line-pattern-height': int,

    # image type: png or tiff, omitted thanks to PIL
    'line-pattern-type': None,

    # metawriter support
    'line-pattern-meta-output': str,

    'line-pattern-meta-writer': str,

    #--------------- shield symbolizer

    # 
    'shield-name': None, # (use selector for this)

    # 
    'shield-face-name': str,

    # Fontset name
    'shield-fontset': str,
    
    # 
    'shield-size': int,

    # 
    'shield-fill': color,

    # Minimum distance between repeated labels such as street names or shield symbols
    'shield-min-distance': int,

    # Spacing between repeated labels such as street names or shield symbols
    'shield-spacing': int,

    # Horizontal spacing between characters (in pixels).
    'shield-character-spacing': int,
    
    # Vertical spacing between lines of multiline shields (in pixels)
    'shield-line-spacing': int,

    # Text offset in pixels from image center
    'shield-text-dx': int,
    'shield-text-dy': int,

    # path to image file (default none)
    'shield-file': uri,

    # px (default 4), generally omit this and let PIL handle it
    'shield-width': int,
    'shield-height': int,

    # image type: png or tiff, omitted thanks to PIL
    'shield-type': None,

    # metawriter support
    'shield-meta-output': str,

    'shield-meta-writer': str,
}

class ParseException(Exception):
    
    def __init__(self, msg, line, col):
        Exception.__init__(self, '%(msg)s (line %(line)d, column %(col)d)' % locals())

class Declaration:
    """ Bundle with a selector, single property and value.
    """
    def __init__(self, selector, property, value, sort_key):
        self.selector = selector
        self.property = property
        self.value = value
        self.sort_key = sort_key

    def __repr__(self):
        return u'%(selector)s { %(property)s: %(value)s }' % self.__dict__

class Selector:
    """ Represents a complete selector with elements and attribute checks.
    """
    def __init__(self, *elements):
        assert len(elements) in (1, 2)
        assert elements[0].names[0] in ('Map', 'Layer') or elements[0].names[0][0] in ('.', '#', '*')
        assert len(elements) == 1 or not elements[1].countTests()
        assert len(elements) == 1 or not elements[1].countIDs()
        assert len(elements) == 1 or not elements[1].countClasses()
    
        self.elements = elements[:]

    def convertZoomTests(self, is_merc=True):
        """ Modify the tests on this selector to use mapnik-friendly
            scale-denominator instead of shorthand zoom.
        """
        # somewhat-fudged values for mapniks' scale denominator at a range
        # of zoom levels when using the Google/VEarth mercator projection.
        zooms = {
             1: (200000000, 500000000),
             2: (100000000, 200000000),
             3: (50000000, 100000000),
             4: (25000000, 50000000),
             5: (12500000, 25000000),
             6: (6500000, 12500000),
             7: (3000000, 6500000),
             8: (1500000, 3000000),
             9: (750000, 1500000),
            10: (400000, 750000),
            11: (200000, 400000),
            12: (100000, 200000),
            13: (50000, 100000),
            14: (25000, 50000),
            15: (12500, 25000),
            16: (5000, 12500),
            17: (2500, 5000),
            18: (1000, 2500),
            19: (500, 1000),
            20: (250, 500),
            21: (100, 250),
            22: (50, 100),
           }
        
        for test in self.elements[0].tests:
            if test.property == 'zoom':
                if not is_merc:
                    # TODO - should we warn instead that values may not be appropriate?
                    raise NotImplementedError('Map srs is not web mercator, so zoom level shorthand cannot be propertly converted to Min/Max scaledenominators')

                test.property = 'scale-denominator'

                if test.op == '=':
                    # zoom level equality implies two tests, so we add one and modify one
                    self.elements[0].addTest(SelectorAttributeTest('scale-denominator', '<', max(zooms[test.value])))
                    test.op, test.value = '>=', min(zooms[test.value])

                elif test.op == '<':
                    test.op, test.value = '>=', max(zooms[test.value])
                elif test.op == '<=':
                    test.op, test.value = '>=', min(zooms[test.value])
                elif test.op == '>=':
                    test.op, test.value = '<', max(zooms[test.value])
                elif test.op == '>':
                    test.op, test.value = '<', min(zooms[test.value])


    def specificity(self):
        """ Loosely based on http://www.w3.org/TR/REC-CSS2/cascade.html#specificity
        """
        ids = sum(a.countIDs() for a in self.elements)
        non_ids = sum((a.countNames() - a.countIDs()) for a in self.elements)
        tests = sum(len(a.tests) for a in self.elements)
        
        return (ids, non_ids, tests)

    def matches(self, tag, id, classes):
        """ Given an id and a list of classes, return True if this selector would match.
        """
        element = self.elements[0]
        unmatched_ids = [name[1:] for name in element.names if name.startswith('#')]
        unmatched_classes = [name[1:] for name in element.names if name.startswith('.')]
        unmatched_tags = [name for name in element.names if name is not '*' and not name.startswith('#') and not name.startswith('.')]
        
        if tag and tag in unmatched_tags:
            unmatched_tags.remove(tag)

        if id and id in unmatched_ids:
            unmatched_ids.remove(id)

        for class_ in classes:
            if class_ in unmatched_classes:
                unmatched_classes.remove(class_)
        
        if unmatched_tags or unmatched_ids or unmatched_classes:
            return False

        else:
            return True
    
    def isRanged(self):
        """
        """
        return bool(self.rangeTests())
    
    def rangeTests(self):
        """
        """
        return [test for test in self.allTests() if test.isRanged()]
    
    def isMapScaled(self):
        """
        """
        return bool(self.mapScaleTests())
    
    def mapScaleTests(self):
        """
        """
        return [test for test in self.allTests() if test.isMapScaled()]
    
    def allTests(self):
        """
        """
        tests = []
        
        for test in self.elements[0].tests:
            tests.append(test)

        return tests
    
    def inRange(self, value):
        """
        """
        for test in self.rangeTests():
            if not test.inRange(value):
                return False

        return True

    def __repr__(self):
        return u' '.join(repr(a) for a in self.elements)

class SelectorElement:
    """ One element in selector, with names and tests.
    """
    def __init__(self, names=None, tests=None):
        if names:
            self.names = names
        else:
            self.names = []

        if tests:
            self.tests = tests
        else:
            self.tests = []

    def addName(self, name):
        self.names.append(str(name))
    
    def addTest(self, test):
        self.tests.append(test)

    def countTests(self):
        return len(self.tests)
    
    def countIDs(self):
        return len([n for n in self.names if n.startswith('#')])
    
    def countNames(self):
        return len(self.names)
    
    def countClasses(self):
        return len([n for n in self.names if n.startswith('.')])
    
    def __repr__(self):
        return u''.join(self.names) + u''.join(repr(t) for t in self.tests)

class SelectorAttributeTest:
    """ Attribute test for a Selector, i.e. the part that looks like "[foo=bar]"
    """
    def __init__(self, property, op, value):
        assert op in ('<', '<=', '=', '!=', '>=', '>')
        self.op = op
        self.property = str(property)
        self.value = value

    def __repr__(self):
        return u'[%(property)s%(op)s%(value)s]' % self.__dict__

    def __cmp__(self, other):
        """
        """
        return cmp(unicode(self), unicode(other))

    def isSimple(self):
        """
        """
        return self.op in ('=', '!=') and not self.isRanged()
    
    def inverse(self):
        """
        
            TODO: define this for non-simple tests.
        """
        assert self.isSimple(), 'inverse() is only defined for simple tests'
        
        if self.op == '=':
            return SelectorAttributeTest(self.property, '!=', self.value)
        
        elif self.op == '!=':
            return SelectorAttributeTest(self.property, '=', self.value)
    
    def isNumeric(self):
        """
        """
        return type(self.value) in (int, float)
    
    def isRanged(self):
        """
        """
        return self.op in ('<', '<=', '>=', '>')
    
    def isMapScaled(self):
        """
        """
        return self.property == 'scale-denominator'
    
    def inRange(self, scale_denominator):
        """
        """
        if not self.isRanged():
            # always in range
            return True

        elif self.op == '>' and scale_denominator > self.value:
            return True

        elif self.op == '>=' and scale_denominator >= self.value:
            return True

        elif self.op == '=' and scale_denominator == self.value:
            return True

        elif self.op == '<=' and scale_denominator <= self.value:
            return True

        elif self.op == '<' and scale_denominator < self.value:
            return True

        return False

    def isCompatible(self, tests):
        """ Given a collection of tests, return false if this test contradicts any of them.
        """
        # print '?', self, tests
        
        for test in tests:
            if self.property == test.property:
                if self.op == '=':
                    if test.op == '=' and self.value != test.value:
                        return False
    
                    if test.op == '!=' and self.value == test.value:
                        return False
    
                    if test.op == '<' and self.value >= test.value:
                        return False
                
                    if test.op == '>' and self.value <= test.value:
                        return False
                
                    if test.op == '<=' and self.value > test.value:
                        return False
                
                    if test.op == '>=' and self.value < test.value:
                        return False
            
                if self.op == '!=':
                    if test.op == '=' and self.value == test.value:
                        return False
    
                    if test.op == '!=':
                        pass
    
                    if test.op == '<':
                        pass
                
                    if test.op == '>':
                        pass
                
                    if test.op == '<=' and self.value == test.value:
                        return False
                
                    if test.op == '>=' and self.value == test.value:
                        return False
            
                if self.op == '<':
                    if test.op == '=' and self.value <= test.value:
                        return False
    
                    if test.op == '!=':
                        return False
    
                    if test.op == '<':
                        pass
                
                    if test.op == '>' and self.value <= test.value:
                        return False
                
                    if test.op == '<=':
                        pass
                
                    if test.op == '>=' and self.value <= test.value:
                        return False
            
                if self.op == '>':
                    if test.op == '=' and self.value >= test.value:
                        return False
    
                    if test.op == '!=':
                        return False
    
                    if test.op == '<' and self.value >= test.value:
                        return False
                
                    if test.op == '>':
                        pass
                
                    if test.op == '<=' and self.value >= test.value:
                        return False
                
                    if test.op == '>=':
                        pass
            
                if self.op == '<=':
                    if test.op == '=' and self.value < test.value:
                        return False
    
                    if test.op == '!=' and self.value == test.value:
                        return False
    
                    if test.op == '<':
                        pass
                
                    if test.op == '>' and self.value <= test.value:
                        return False
                
                    if test.op == '<=':
                        pass
                
                    if test.op == '>=' and self.value < test.value:
                        return False
            
                if self.op == '>=':
                    if test.op == '=' and self.value > test.value:
                        return False
    
                    if test.op == '!=' and self.value == test.value:
                        return False
    
                    if test.op == '<' and self.value >= test.value:
                        return False
                
                    if test.op == '>':
                        pass
                
                    if test.op == '<=' and self.value > test.value:
                        return False
                
                    if test.op == '>=':
                        pass

        return True
    
    def rangeOpEdge(self):
        ops = {'<': operator.lt, '<=': operator.le, '=': operator.eq, '>=': operator.ge, '>': operator.gt}
        return ops[self.op], self.value

        return None

class Property:
    """ A style property.
    """
    def __init__(self, name):
        assert name in properties
    
        self.name = name

    def group(self):
        return self.name.split('-')[0]
    
    def __repr__(self):
        return self.name

    def __str__(self):
        return repr(self)

class Value:
    """ A style value.
    """
    def __init__(self, value, important):
        self.value = value
        self.important = important

    def importance(self):
        return int(self.important)
    
    def __repr__(self):
        return repr(self.value)

    def __str__(self):
        return str(self.value)

def stylesheet_declarations(string, is_merc=False):
    """ Parse a string representing a stylesheet into a list of declarations.
    
        Required boolean is_merc indicates whether the projection should
        be interpreted as spherical mercator, so we know what to do with
        zoom/scale-denominator in postprocess_selector().
    """
    declarations = []
    tokens = cssTokenizer().tokenize(string)
    
    while True:
        try:
            for declaration in parse_rule(tokens, []):
                declarations.append(declaration)
        except StopIteration:
            break
    
    # sort by a css-like method
    return sorted(declarations, key=operator.attrgetter('sort_key'))

def stylesheet_rulesets(string, is_merc=False):
    """ Parse a string representing a stylesheet into a list of rulesets.
    
        Required boolean is_merc indicates whether the projection should
        be interpreted as spherical mercator, so we know what to do with
        zoom/scale-denominator in postprocess_selector().
    """
    in_selectors = False
    in_block = False
    in_declaration = False # implies in_block
    in_property = False # implies in_declaration
    
    rulesets = []
    tokens = cssTokenizer().tokenize(string)
    
    for token in tokens:
        nname, value, line, col = token
        
        try:
            if not in_selectors and not in_block:
                if nname == 'CHAR' and value == '{':
                    # 
                    raise ParseException('Encountered unexpected opening "{"', line, col)

                elif (nname in ('IDENT', 'HASH')) or (nname == 'CHAR' and value != '{'):
                    # beginning of a 
                    rulesets.append({'selectors': [[(nname, value)]], 'declarations': []})
                    in_selectors = True
                    
            elif in_selectors and not in_block:
                ruleset = rulesets[-1]
            
                if (nname == 'CHAR' and value == '{'):
                    # open curly-brace means we're on to the actual rule sets
                    ruleset['selectors'][-1] = postprocess_selector(ruleset['selectors'][-1], is_merc, line, col)
                    in_selectors = False
                    in_block = True
    
                elif (nname == 'CHAR' and value == ','):
                    # comma means there's a break between selectors
                    ruleset['selectors'][-1] = postprocess_selector(ruleset['selectors'][-1], is_merc, line, col)
                    ruleset['selectors'].append([])
    
                elif nname not in ('COMMENT'):
                    # we're just in a selector is all
                    ruleset['selectors'][-1].append((nname, value))
    
            elif in_block and not in_declaration:
                ruleset = rulesets[-1]
            
                if nname == 'IDENT':
                    # right at the start of a declaration
                    ruleset['declarations'].append({'property': [(nname, value)], 'value': [], 'position': (line, col)})
                    in_declaration = True
                    in_property = True
                    
                elif (nname == 'CHAR' and value == '}'):
                    # end of block
                    in_block = False

                elif nname not in ('S', 'COMMENT'):
                    # something else
                    raise ParseException('Unexpected %(nname)s while looking for a property' % locals(), line, col)
    
            elif in_declaration and in_property:
                declaration = rulesets[-1]['declarations'][-1]
            
                if nname == 'CHAR' and value == ':':
                    # end of property
                    declaration['property'] = postprocess_property(declaration['property'], line, col)
                    in_property = False
    
                elif nname not in ('COMMENT'):
                    # in a declaration property
                    declaration['property'].append((nname, value))
    
            elif in_declaration and not in_property:
                declaration = rulesets[-1]['declarations'][-1]
            
                if nname == 'CHAR' and value == ';':
                    # end of declaration
                    declaration['value'] = postprocess_value(declaration['value'], declaration['property'], line, col)
                    in_declaration = False
    
                elif nname not in ('COMMENT'):
                    # in a declaration value
                    declaration['value'].append((nname, value))

        except ParseException, e:
            #raise ParseException(e.message + ' (line %(line)d, column %(col)d)' % locals(), line, col)
            raise

    return rulesets

def rulesets_declarations(rulesets):
    """ Convert a list of rulesets (as returned by stylesheet_rulesets)
        into an ordered list of individual selectors and declarations.
    """
    declarations = []
    
    for ruleset in rulesets:
        for declaration in ruleset['declarations']:
            for selector in ruleset['selectors']:
                declarations.append(Declaration(selector, declaration['property'], declaration['value'],
                                                (declaration['value'].importance(), selector.specificity(), declaration['position'])))

    # sort by a css-like method
    return sorted(declarations, key=operator.attrgetter('sort_key'))

def trim_extra(tokens):
    """ Trim comments and whitespace from each end of a list of tokens.
    """
    if len(tokens) == 0:
        return tokens
    
    while tokens[0][0] in ('S', 'COMMENT'):
        tokens = tokens[1:]

    while tokens[-1][0] in ('S', 'COMMENT'):
        tokens = tokens[:-1]
        
    return tokens

def parse_attribute(tokens):

    def next_scalar(tokens):
        while True:
            tname, tvalue, line, col = tokens.next()
            if tname == 'NUMBER':
                return tvalue
            elif tname == 'STRING':
                return tvalue[1:-1]
            elif tname != 'S':
                raise ParseException('', line, col)
    
    def finish_attribute(tokens):
        while True:
            tname, tvalue, line, col = tokens.next()
            if (tname, tvalue) == ('CHAR', ']'):
                return
            elif tname != 'S':
                raise ParseException('', line, col)
    
    while True:
        tname, tvalue, line, col = tokens.next()
        
        if tname == 'IDENT':
            property = tvalue
            
            while True:
                tname, tvalue, line, col = tokens.next()
                
                if (tname, tvalue) in [('CHAR', '<'), ('CHAR', '>')]:
                    _tname, _tvalue, line, col = tokens.next()
        
                    if (_tname, _tvalue) == ('CHAR', '='):
                        #
                        # One of <=, >=
                        #
                        op = tvalue + _tvalue
                        value = next_scalar(tokens)
                        finish_attribute(tokens)
                        return SelectorAttributeTest(property, op, value)
                    
                    else:
                        #
                        # One of <, > and we popped a token too early
                        #
                        op = tvalue
                        value = next_scalar(chain([(_tname, _tvalue, line, col)], tokens))
                        finish_attribute(tokens)
                        return SelectorAttributeTest(property, op, value)
                
                elif (tname, tvalue) == ('CHAR', '!'):
                    _tname, _tvalue, line, col = tokens.next()
        
                    if (_tname, _tvalue) == ('CHAR', '='):
                        #
                        # !=
                        #
                        op = tvalue + _tvalue
                        value = next_scalar(tokens)
                        finish_attribute(tokens)
                        return SelectorAttributeTest(property, op, value)
                    
                    else:
                        raise ParseException('', line, col)
                
                elif (tname, tvalue) == ('CHAR', '='):
                    #
                    # =
                    #
                    op = tvalue
                    value = next_scalar(tokens)
                    finish_attribute(tokens)
                    return SelectorAttributeTest(property, op, value)
                
                elif tname != 'S':
                    raise ParseException('', line, col)
        
        elif tname != 'S':
            raise ParseException('', line, col)

    raise ParseException('', line, col)

def postprocess_value(property, tokens, important, line, col):
    
    if properties[property.name] in (int, float, str, color, uri, boolean) or type(properties[property.name]) is tuple:
        if len(tokens) != 1:
            raise ParseException('Single value only for property "%(property)s"' % locals(), line, col)

    if properties[property.name] is int:
        if tokens[0][0] != 'NUMBER':
            raise ParseException('Number value only for property "%(property)s"' % locals(), line, col)

        value = int(tokens[0][1])

    elif properties[property.name] is float:
        if tokens[0][0] != 'NUMBER':
            raise ParseException('Number value only for property "%(property)s"' % locals(), line, col)

        value = float(tokens[0][1])

    elif properties[property.name] is str:
        if tokens[0][0] != 'STRING':
            raise ParseException('String value only for property "%(property)s"' % locals(), line, col)

        value = str(tokens[0][1][1:-1])

    elif properties[property.name] is color_transparent:
        if tokens[0][0] != 'HASH' and (tokens[0][0] != 'IDENT' or tokens[0][1] != 'transparent'):
            raise ParseException('Hash or transparent value only for property "%(property)s"' % locals(), line, col)

        if tokens[0][0] == 'HASH':
            if not re.match(r'^#([0-9a-f]{3}){1,2}$', tokens[0][1], re.I):
                raise ParseException('Unrecognized color value for property "%(property)s"' % locals(), line, col)
    
            hex = tokens[0][1][1:]
            
            if len(hex) == 3:
                hex = hex[0]+hex[0] + hex[1]+hex[1] + hex[2]+hex[2]
            
            rgb = (ord(unhex(h)) for h in (hex[0:2], hex[2:4], hex[4:6]))
            
            value = color(*rgb)

        else:
            value = 'transparent'

    elif properties[property.name] is color:
        if tokens[0][0] != 'HASH':
            raise ParseException('Hash value only for property "%(property)s"' % locals(), line, col)

        if not re.match(r'^#([0-9a-f]{3}){1,2}$', tokens[0][1], re.I):
            raise ParseException('Unrecognized color value for property "%(property)s"' % locals(), line, col)

        hex = tokens[0][1][1:]
        
        if len(hex) == 3:
            hex = hex[0]+hex[0] + hex[1]+hex[1] + hex[2]+hex[2]
        
        rgb = (ord(unhex(h)) for h in (hex[0:2], hex[2:4], hex[4:6]))
        
        value = color(*rgb)

    elif properties[property.name] is uri:
        if tokens[0][0] != 'URI':
            raise ParseException('URI value only for property "%(property)s"' % locals(), line, col)

        raw = str(tokens[0][1])

        if raw.startswith('url("') and raw.endswith('")'):
            raw = raw[5:-2]
            
        elif raw.startswith("url('") and raw.endswith("')"):
            raw = raw[5:-2]
            
        elif raw.startswith('url(') and raw.endswith(')'):
            raw = raw[4:-1]

        value = uri(raw)
            
    elif properties[property.name] is boolean:
        if tokens[0][0] != 'IDENT' or tokens[0][1] not in ('true', 'false'):
            raise ParseException('true/false value only for property "%(property)s"' % locals(), line, col)

        value = boolean(tokens[0][1] == 'true')
            
    elif type(properties[property.name]) is tuple:
        if tokens[0][0] != 'IDENT':
            raise ParseException('Identifier value only for property "%(property)s"' % locals(), line, col)

        if tokens[0][1] not in properties[property.name]:
            raise ParseException('Unrecognized value for property "%(property)s"' % locals(), line, col)

        value = str(tokens[0][1])
            
    elif properties[property.name] is numbers:
        values = []
        
        # strip the list down to what we think goes number, comma, number, etc.
        relevant_tokens = [token for token in tokens
                           if token[0] == 'NUMBER' or token == ('CHAR', ',')]
        
        for (i, token) in enumerate(relevant_tokens):
            if (i % 2) == 0 and token[0] == 'NUMBER':
                try:
                    value = int(token[1])
                except ValueError:
                    value = float(token[1])

                values.append(value)

            elif (i % 2) == 1 and token[0] == 'CHAR':
                # fine, it's a comma
                continue

            else:
                raise ParseException('Value for property "%(property)s" should be a comma-delimited list of numbers' % locals(), line, col)

        value = numbers(*values)

    return Value(value, important)

def parse_block(tokens):
    """ Return an array of tuples: (property, value, (line, col), importance)
    """
    def parse_value(tokens):
        value = []
        while True:
            tname, tvalue, line, col = tokens.next()
            if (tname, tvalue) == ('CHAR', '!'):
                while True:
                    tname, tvalue, line, col = tokens.next()
                    if (tname, tvalue) == ('IDENT', 'important'):
                        while True:
                            tname, tvalue, line, col = tokens.next()
                            if (tname, tvalue) == ('CHAR', ';'):
                                #
                                # end of a high-importance value
                                #
                                return value, True
                            elif tname != 'S':
                                raise ParseException('', line, col)
                        break
                    else:
                        raise ParseException('', line, col)
                break
            elif (tname, tvalue) == ('CHAR', ';'):
                #
                # end of a low-importance value
                #
                return value, False
            elif tname != 'S':
                value.append((tname, tvalue))
        raise ParseException('', line, col)
    
    property_values = []
    
    while True:
        tname, tvalue, line, col = tokens.next()
        
        if tname == 'IDENT':
            _tname, _tvalue, _line, _col = tokens.next()
            
            if (_tname, _tvalue) == ('CHAR', ':'):
            
                if tvalue not in properties:
                    raise ParseException('', line, col)

                property = Property(tvalue)
                vtokens, importance = parse_value(tokens)
                value = postprocess_value(property, vtokens, importance, line, col)
                
                property_values.append((property, value, (line, col), importance))
                
            else:
                raise ParseException('', line, col)
        
        elif (tname, tvalue) == ('CHAR', '}'):
            return property_values
        
        elif tname != 'S':
            raise ParseException('', line, col)

    raise ParseException('', line, col)

def parse_rule(tokens, selectors):

    element = None
    elements = []
    
    while True:
        tname, tvalue, line, col = tokens.next()
        
        if tname == 'IDENT':
            #
            # Identifier always starts a new element.
            #
            element = SelectorElement()
            elements.append(element)
            element.addName(tvalue)
            
        elif tname == 'HASH':
            #
            # Hash is an ID selector:
            # http://www.w3.org/TR/CSS2/selector.html#id-selectors
            #
            if not element:
                element = SelectorElement()
                elements.append(element)
        
            element.addName(tvalue)
        
        elif (tname, tvalue) == ('CHAR', '.'):
            while True:
                tname, tvalue, line, col = tokens.next()
                
                if tname == 'IDENT':
                    #
                    # Identifier after a period is a class selector:
                    # http://www.w3.org/TR/CSS2/selector.html#class-html
                    #
                    if not element:
                        element = SelectorElement()
                        elements.append(element)
                
                    element.addName('.'+tvalue)
                    break
                
                else:
                    raise ParseException('', line, col)
        
        elif (tname, tvalue) == ('CHAR', '*'):
            #
            # Asterisk character is a universal selector:
            # http://www.w3.org/TR/CSS2/selector.html#universal-selector
            #
            if not element:
                element = SelectorElement()
                elements.append(element)
        
            element.addName(tvalue)

        elif (tname, tvalue) == ('CHAR', '['):
            #
            # Left-bracket is the start of an attribute selector:
            # http://www.w3.org/TR/CSS2/selector.html#attribute-selectors
            #
            test = parse_attribute(tokens)
            element.addTest(test)
        
        elif (tname, tvalue) == ('CHAR', ','):
            #
            # Comma delineates one of a group of selectors:
            # http://www.w3.org/TR/CSS2/selector.html#grouping
            #
            # Recurse here.
            #
            selectors.append(Selector(*elements))
            return parse_rule(tokens, selectors)
        
        elif (tname, tvalue) == ('CHAR', '{'):
            #
            # Left-brace is the start of a block:
            # http://www.w3.org/TR/CSS2/syndata.html#block
            #
            # Return a full block here.
            #
            selectors.append(Selector(*elements))
            ruleset = []
            
            for (selector, property_value) in product(selectors, parse_block(tokens)):

                property, value, (line, col), importance = property_value
                sort_key = value.importance(), selector.specificity(), (line, col)

                ruleset.append(Declaration(selector, property, value, sort_key))
            
            return ruleset
