from distutils.core import setup
import sys

py_version_t = sys.version_info[:2]
py_version_s = ".".join([str(x) for x in py_version_t])

assert py_version_s in ("2.5", "2.6"), "Python version 2.5 or 2.6 required"

if __name__ == '__main__':
    setup(
        name = 'generator_tools',
        version = '0.3.6',
        description = 'generator_tools enable copying and pickling generators',
        author = 'Kay Schluehr',
        author_email = 'kay@fiber-space.de',
        url = 'http://www.fiber-space.de/',
        download_url = 'http://www.fiber-space.de/downloads/download.html',
        license = "BSD",
        packages = ['generator_tools',
                    'generator_tools.tests',
                    ],
        package_data={'': ['LICENSE.txt'],
                      'generator_tools': ['doc/*.html',
                                          'doc/*.png']},
    )

