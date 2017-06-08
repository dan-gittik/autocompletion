# Autocompletion

A Bash autocompletion framework implemented in Python, which makes it easy to define, and even extend, how your
commands are autocompleted.

## Installation

1. Download ``autocompleter.py``.

   ```console
   $ wget https://raw.githubusercontent.com/dan-gittik/autocompleter/master/autocompleter.py -O ~/.autocompleter.py
   ```

2. Source ``autocompleter.py`` (yeah, it's a Bash script as well!).

   ```console
   $ source ~/.autocompleter.py
   ```

   You might want to add this to your ``.bashrc`` or ``.profile``:

   ```console
   $ echo "source ~/.autocompleter.py" >> ~/.bashrc
   ```
   
## Usage

Once you've sourced ``autocompleter.py``, the ``autocomplete`` function should become available.

```console
$ autocomplete
USAGE: autocomplete <command> <config-path>
```

Call it on the command you want autocompleted and the path to its autocompletion specifications file.
For example:

```console
$ cat spec.py
# one --foo --bar
# two <path>

$ autocomplete prog spec.py

$ prog <TAB>
one  two
$ prog one --<TAB>
--foo  --bar
$ prog two <TAB>
dir/  file.txt
```

The autocompletion specifications file format is pretty simple: it's a Python module whose first comments are
interpreted as autocompletion specifications, starting with a subcommand (e.g. ``one`` or ``two``), and then
flags (e.g. ``--foo``) and/or arguments (e.g. ``<path>``).

Flags are autocompleted once the user has typed ``-``, and can be boolean (e.g. ``--flag``) or have a value (e.g.
``--flag=<value>``). Boolean flags are autocompleted as-is, whereas flags with values are autocompleted until the
``=``, and then their value is autocompleted like an argument.

Flags are only autocompleted once; that is, if ``--foo`` was already typed, it will not be offered for autocompletion
again.

Arguments are autocompleted using a **completer** of a similar name: for example, ``<value>`` is a "dummy" completer
that offers no autocompletions, and ``<path>`` is a completer that offers entries in the current directory (including
filesystem traversal, of course).

So, for example, if a user wants to use the ``decrypt`` subcommand, which takes a password (which makes no sense to
autocomplete) and a path, its autocompletion specification will be ``# decrypt <value> <path>``.

The cool thing about this framework is how easy it is to define completers of your own: all you have to do is implement
a ``complete_something(arg, word)`` function, and it will be called to autocomplete ``<something>`` arguments (and flag
values)!

A completer function receives ``arg``, which is a complex object for advanced usage (covered later), and ``prefix``,
which is whatever the user has typed so far; and returns a list of strings the are considered as autocompletion
options. For example:

```python
# subcommand <color>

colors = 'red', 'yellow', 'green', 'blue'

def complete_color(arg, prefix):
    return [color for color in colors if color.startswith(word)]
```

In fact, the framework filters options starting with the prefix on its own, so this can be made even shorter:

```python
# subcommand <color>

def complete_color(arg, prefix):
    return ['red', 'yellow', 'green', 'blue']
```

However, the ``prefix`` comes in handy when we want to filter options ourselves for efficiency reasons, like when
querying a database:

```python
# subcommand <user>

def complete_user(arg, prefix):
    query = 'SELECT username FROM users WHERE username LIKE ?'
    with sqlite3.connect('users.db') as con:
        return [row[0] for row in con.execute(query, (prefix+'%',))]
```

## Advanced Usage

The ``arg`` object can be used to access the entire autocompletion state, which can be useful for complex
autocompletions that depend on the subcommand or other flags or arguments.

In case of a flag value autocompletion, ``arg`` is a ``Flag`` object with a ``name`` (e.g. ``--foo``), a ``value``
(e.g. ``<value>``), and a ``subcommand``. In case of an argument autocompletion, ``arg`` is an ``Argument`` object
with a ``name`` (e.g. ``<path>``) and a ``subcommand``.

In both cases, ``subcommand`` is a ``Subcommand`` object with a ``name`` (e.g. ``one``), a ``words`` list of all the
flags and arguments it supports, and the same list split into a ``flags`` dictionary and an ``arguments`` list.

Furthermore, it has an ``autocompleter`` attribute, which is an ``Autocompleter`` object with the ``line`` typed by
the user, the ``cursor`` position in it, the same line split into a ``words`` list, and the ``index`` of the current
word.

So, for example, to get the previous word, one would do:

```python
# subcommand <example>

def complete_example(arg, prefix):
    prev = arg.subcommand.autocompleter.words[arg.subcommand.autocompleter.index-1]
    # Do stuff...
```

Notice that the previous word is not necessarily the previous argument, because flags can be inserted anywhere. So,
to get the previous argument, one would use ``subcommand``'s ``argument_index`` (available only when autocompleting
arguments!):

```python
# subcommand <arg1> <arg2>

def complete_arg2(arg, prefix):
    arg1 = args.subcommand.autocompleter.words[arg.subcommand.argument_index-1]
    # Do stuff...
```

To react differently to different subcommands, one would do:

```python
# one <example>
# two <example>

def complete_example(arg, prefix):
    if arg.subcommand.name == 'one':
        # Do stuff...
    if arg.subcommand.name == 'two':
        # Do stuff...
```

``autocompleter`` also has a ``compopt`` attribute, which is a list of options that cannot be applied in Python, and
therefore must be passed on to Bash and executed there on-demand. The two interesting options are:

1. ``filenames``, which makes Bash treat the autocompletion options as paths, and only display their filenames (from
   the last slash on). So, for example, when you type ``../``, instead of offering ``../dir`` and ``../file.txt``, it
   offers just ``dir`` and ``file.txt``.

   (This option is used by the ``<path>`` completer.)

2. ``nospace``, which makes Bash not add a space and move on to the next argument when only one autocompletion option
   is left.

   (This option is used by flags with values; otherwise, Bash would add a space after the ``=``, as in ``--flag= ``,
   and skip the value autocompletion.)

So, if you need to set these or other ``compopt`` options:

```python
# subcommand <example>

def complete_example(arg, prefix):
    arg.subcommand.autocompleter.compopt.append('option')
    # Do stuff...
```
