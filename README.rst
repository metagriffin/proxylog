========
ProxyLog
========

A simple HTTP proxy server that logs all client/server communications,
with some added features to parse the content such as automatic
gunzipping, output colorization and known data "pretty" formatting,
including XML, JSON, and YAML.


Project
=======

* Homepage: https://github.com/metagriffin/proxylog
* Bugs: https://github.com/metagriffin/proxylog/issues


TL;DR
=====

Install:

.. code-block:: bash

  $ pip install proxylog

Proxy http://www.example.com/ locally to http://localhost:8080/, log
all transactions to a file and display them colorized and formatted
on the console:

.. code-block:: bash

  $ proxylog -r www.example.com:80 -p 8080 -o transactions.log -dcf

Display a previous log file colorized and formatted:

.. code-block:: bash

  $ proxylog -i transactions.log -dcf


Colorizing
==========

The colorizing is done via the `Pygments
<https://pypi.python.org/pypi/Pygments>`_ package; proxylog's
``--theme`` option is passed through to pygments, so any of the color
themes that pygments supports can be used. Use the following command
to list the available themes:

.. code-block:: bash

  $ pygmentize -L styles


Formatting
==========

"Formatting" refers to proxylog's ability to re-format known data
formats to a more human-friendly display, which when combined with
colorization, can yield very readable data. *HOWEVER*, this does
alter the actual data, so if you are using the data in any way,
you should not use the "--format" flag.

Currently, the following formats are supported, with examples of how
they are "prettified":

* XML:

  Input:

  .. code-block:: text

    <root  ><node   attr= "value">data</node>
      </root>

  Formatted output:

  .. code-block:: text

    <root>
      <node attr="value">data</node>
    </root>

* JSON:

  Input:

  .. code-block:: text

    {"key": "value", "list": [3, "bar", null, "foo"]}

  Formatted output:

  .. code-block:: text

    {
      "key": "value",
      "list": [
        3,
        "bar",
        null,
        "foo"
      ]
    }

* YAML:

  Input:

  .. code-block:: text

    {key: value, list: [3, bar, null, foo]}

  Formatted output:

  .. code-block:: text

    {
      "key": "value",
      "list": [
        3,
        "bar",
        null,
        "foo"
      ]
    }
