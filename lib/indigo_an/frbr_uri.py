import re

WORK_URI_RE = re.compile(r"""^/(?P<country>[a-z]{2})       # country
                              /(?P<nature>[^/]+)           # document type
                              /((?P<subtype>[^/]+)         # subtype (optional)
                              /((?P<actor>[^/]+)/)?)?      # actor (optional)
                              (?P<date>[0-9]{4}(-[0-9]{2}(-[0-9]{2})?)?)  # date
                              /(?P<number>[^/]+)           # number
                              """, re.X)

class FrbrUri(object):
    """
    An FRBR URI parser.

    .. seealso::

       http://akresolver.cs.unibo.it/admin/documentation.html
       http://www.akomantoso.org/release-notes/akoma-ntoso-3.0-schema/naming-conventions-1/bungenihelpcenterreferencemanualpage.2008-01-09.1484954524
    """

    def __init__(self, country, nature, subtype, actor, date, number):
        self.country = country
        self.nature = nature
        self.subtype = subtype
        self.actor = actor
        self.date = date
        self.number = number

    def __str__(self):
        parts = ['', self.country, self.nature]

        if self.subtype:
            parts.append(self.subtype)
            if self.actor:
                parts.append(self.actor)
        
        parts += [self.date, self.number]
        return '/'.join(parts)

    @classmethod
    def parse(cls, s):
        match = WORK_URI_RE.match(s)
        if match:
            return cls(**match.groupdict())
        else:
            raise ValueError("Invalid FRBR URI")

        # TODO: handle the expression components (language, date, etc.)
        # TODO: handle the components (schedules etc.)
