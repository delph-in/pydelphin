import re
from urllib.parse import urljoin

from docutils import nodes


def setup(app):
    app.add_role('wiki', wikilink)
    app.add_config_value('wiki_url', None, 'env')


def wikilink(name, rawtext, text, lineno, inliner, options={}, content=[]):
    base = inliner.document.settings.env.app.config.wiki_url
    match = re.search(r'(.*)\s+<(.*)>', text)
    if match:
        text, slug = match.groups()
        text = text.strip()
        slug = slug.strip()
    else:
        text = text.strip()
        slug = text
    url = urljoin(base, slug)
    node = nodes.reference(rawtext, text, refuri=url, **options)
    return [node], []
