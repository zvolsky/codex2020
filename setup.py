# this is not ready and setup.py is here now just to list external references (install_requires=..)

from distutils.core import setup
setup(
  name = 'codex2020',
  py_modules = ['xxxx'],
  version = '0.1.0',
  description = 'software for libraries and book market',
  install_requires = ['pymarc', 'PyZ3950'],
	# PyZ3950: z https://github.com/alexsdutton/PyZ3950,
	#	pak: python setup.py install,
	#	pak: make the first import from Py with root privileges (will create something?) <- need fix!
    # pymarc: from PyPI
    #   if: 'module' object has no attribute 'python_2_unicode_compatible'
    #   then try: pip install six --upgrade
  author = 'Mirek Zvolsky',
  author_email = 'zvolsky@seznam.cz',
  url = 'https://github.com/zvolsky/codex2020',
  download_url = 'https://github.com/zvolsky/codex2020/tarball/x.x.x',
  keywords = ['libraries', 'library', 'books', 'book', 'reading'],
  classifiers=[
      'Development Status :: 5 - Production/Stable',
      'Topic :: Office/Business :: Financial :: Accounting',
      'Intended Audience :: Developers',
      'Intended Audience :: Financial and Insurance Industry',
      'License :: OSI Approved :: MIT License',
      'Operating System :: OS Independent',
      'Programming Language :: Python',
      'Topic :: Software Development',
      'Programming Language :: Python :: 2',
  ],
) 
