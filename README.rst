========
ProxyLog
========

A simple HTTP proxy server that logs all client/server communications,
with some added features to parse the content such as automatic
gunzipping, XML pretty-printing and output colorization.


TL;DR
=====

Install:

.. code-block:: bash

  $ pip install proxylog

Proxy http://www.example.com/ locally to http://localhost:8080/, log
all transactions to a file and display them colorized and prettified
on the console:

.. code-block:: bash

  $ proxylog -r www.example.com:80 -p 8080 -o transactions.log -dcx

Display a previous log file colorized and prettified:

.. code-block:: bash

  $ proxylog -i transactions.log -dcx

