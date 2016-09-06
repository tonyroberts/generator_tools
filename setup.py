from setuptools import setup
import sys

assert sys.version_info[:2] == (2,7)

if __name__ == '__main__':
    setup(
        name = 'generator_tools',
        version = '0.4.dev.0',
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
        classifiers=[
            'Programming Language :: Python :: 2.7'
        ]
    )
