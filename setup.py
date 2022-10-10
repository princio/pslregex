#!/usr/bin/env python
# -*- coding: utf-8 -*-

import codecs
from setuptools import setup

description = codecs.open('README.md', encoding='utf-8').read()

setup(name="pslregex",
      version="0.7.11",
      packages=["pslregex"],
      package_data={
          "pslregex": []
    },
      author="princio",
      author_email="l.principi8@gmail.com",
      description="parse suffixes from publicsuffixlist with regex for high perfomances",
      long_description=description,
      long_description_content_type="text/markdown",
      url="https://github.com/princio/pslregex",
      classifiers=[
          "Development Status :: 3 - Alpha",
          "License :: OSI Approved :: Mozilla Public License 2.0 (MPL 2.0)",
          "Topic :: Internet :: Name Service (DNS)",
          "Topic :: Text Processing :: Filters",
          "Operating System :: OS Independent",
        ],
      python_requires=">=3.8.0",
      install_requires=[
          "pandas>=1.4.1",
          "requests>=2.24.0"
      ],
      extras_require={},
      entry_points={
          "console_scripts": [
              "pslregex-init = pslregex.__init__:init",
              "pslregex-update = pslregex.__init__:update",
              "pslregex-test = pslregex.__init__:test",
          ]},
      license='MPL-2.0',
      )