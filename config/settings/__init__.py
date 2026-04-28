import os
from .dev import *

# Use production settings if DJANGO_ENV is set to production
if os.environ.get('DJANGO_ENV') == 'dev':
    from .prod import *
