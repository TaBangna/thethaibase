# pelicanconf.py
AUTHOR = 'The Thai Base'
SITENAME = 'TheThaiBase.com'
SITEURL = ''  # Adjust as necessary
DEFAULT_DATE_FORMAT = '%Y-%m-%d'
PATH = 'content'
PAGE_PATHS = ['pages']
ARTICLE_PATHS = ['articles','hotels', 'guides']
STATIC_PATHS = ['images']
# Set the SITELOGO variable to point to your logo image.
# Ensure the path is relative to your output directory.
SITELOGO = 'images/Logo2.png'
TIMEZONE = 'Asia/Bangkok'
DEFAULT_LANG = 'en'
THEME = 'pelican-themes/Flex'
INDEX_SAVE_AS = 'blog-index.html'
PLUGIN_PATHS = ['pelican-plugins']
PLUGINS = ['jinja2content']

# Enable HTML inside markdown
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
    },
    'output_format': 'html5',
}

from pelican import signals

def add_articles(generator):
    # Make sure the articles attribute exists, then inject into context.
    if hasattr(generator, 'articles'):
        generator.context['articles'] = generator.articles
    else:
        generator.context['articles'] = []

signals.article_generator_finalized.connect(add_articles)
