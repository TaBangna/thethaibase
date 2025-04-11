# pelicanconf.py
AUTHOR = 'The Thai Base'
SITENAME = 'TheThaiBase.com'
SITEURL = "http://localhost:8000"  # Adjust as necessary

PATH = 'content'
PAGE_PATHS = ['pages']
ARTICLE_PATHS = ['articles']
STATIC_PATHS = ['images']
# Set the SITELOGO variable to point to your logo image.
# Ensure the path is relative to your output directory.
SITELOGO = '/images/Logo2.png'
TIMEZONE = 'Asia/Bangkok'
DEFAULT_LANG = 'en'

THEME = 'pelican-themes/Flex'

# Enable HTML inside markdown
MARKDOWN = {
    'extension_configs': {
        'markdown.extensions.extra': {},
        'markdown.extensions.meta': {},
    },
    'output_format': 'html5',
}
