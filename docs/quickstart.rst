#############
Installation
#############

To install the library:

.. code-block:: console

  $ pip install scribe

You will also need to install redis. On Ubuntu:

.. code-block:: console

  $ sudo apt update
  $ sudo apt install redis-server
  $ sudo systemctl status redis-server


######
Usage
######

Generate the default configuration file:

.. code-block:: console

  $ scribe config generate  # will print the path to the generated file

The current default configuration is as follows:

.. literalinclude:: ../scribe/scribe.yaml
  :linenos:
  :language: YAML

Once you are done with any changes to the default configuration, you can start
the worker:

.. code-block:: console

  $ scribe start

The applications can now subscribe to the relevant topics.
