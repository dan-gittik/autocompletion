''':'
autocomplete()
{
    if [ $# != 2 ]
    then
        echo "USAGE: autocomplete <command> <config-path>"
        return 1
    fi
    local COMMAND="$1"
    local CONFIG_PATH="$(readlink -f "$2")"
    eval "
        _complete_$COMMAND()
        {
            local THIS_FILE=\"\$(readlink -f \"\${BASH_SOURCE[0]}\")\"
            COMPREPLY=( \$(python \"\$THIS_FILE\" \"$CONFIG_PATH\" \"\$COMP_LINE\" \"\$COMP_POINT\" \"\$COMP_CWORD\") );
            # Some special behaviour (like displaying path autocompletion only from the last slash on)
            # must be done in bash on-demand, so the first line is reserved for compopt.
            for FLAG in \$(echo \"\${COMPREPLY[0]}\" | tr ',' '\\n')
            do
                if [ \"\$FLAG\" = \".\" ]
                then
                    continue
                fi
                compopt -o \"\$FLAG\"
            done
            COMPREPLY=( \"\${COMPREPLY[@]:1}\" )
        }
        complete -F _complete_$COMMAND $COMMAND
    "
}
return
'''

import collections
import os
import shlex
import sys
import traceback
import types


completers       = {}
completer_prefix = 'complete_'


class Autocompleter(object):

    def __init__(self, config_path, line, cursor, index):
        self.line   = line
        self.cursor = cursor
        self.index  = index
        # Parse the current state.
        self.words = split(self.line)
        # Bash considers '=' a delimiter, but we consider it part of a word, so fix the index.
        #   '=' in the end ('--flag=' => '--flag', '=') requires -1.
        #   '=' in the middle ('--flag=value' => '--flag', '=', 'value') requires -2.
        for word in self.words:
            if word.endswith('='):
                self.index -= 1
            elif '=' in word:
                self.index -= 2
        # Find the current prefix (we can't just use self.words[index] because the cursor may be positioned
        # in the middle of that word, so slice the remainder of the line first).
        before = split(self.line[:self.cursor])
        if self.index < len(before):
            self.prefix = before[self.index]
        else:
            self.prefix = ''
        # Import config as a module and collect its completers.
        self.module = import_module(config_path)
        for key, value in vars(self.module).items():
            if key.startswith(completer_prefix):
                name = key[len(completer_prefix):]
                completers[name] = value
        # Parse config's comments for the autocompletion specifications.
        self.subcommands = collections.OrderedDict()
        with open(config_path) as reader:
            for line in reader:
                line = line.strip()
                if not line:
                    continue
                if not line.startswith('#'):
                    break
                line = line[1:].strip()
                if not line:
                    continue
                subcommand = Subcommand(self, line)
                self.subcommands[subcommand.name] = subcommand
        # Some special behaviour (like displaying path autocompletion only from the last slash on)
        # must be done in bash on-demand, so the first line is reserved for compopt.
        self.compopt = ['.']

    def autocomplete(self):
        # Index 0 is the command, so there's nothing to do.
        if self.index == 0:
            return []
        # Index 1 is the subcommand, so autocomplete all the subcommands starting with the prefix.
        if self.index == 1:
            return [subcommand for subcommand in self.subcommands if subcommand.startswith(self.prefix)]
        # Otherwise, it's a flag or an argument of a subcommand, so delegate autocompletion to it.
        subcommand = self.words[1]
        if subcommand not in self.subcommands:
            return []
        options = self.subcommands[subcommand].autocomplete()
        return [option for option in options if option and option.startswith(self.prefix)]


class Subcommand(object):
    
    def __init__(self, autocompleter, config):
        self.autocompleter = autocompleter
        self.words         = config.split()
        self.name          = self.words[0]
        self.flags         = {}
        self.arguments     = []
        for word in self.words[1:]:
            if word.startswith('-'):
                flag = Flag(self, word)
                self.flags[flag.name] = flag
            else:
                argument = Argument(self, word)
                self.arguments.append(argument)

    def autocomplete(self):
        # '-' means it's a flag.
        if self.autocompleter.prefix.startswith('-'):
            # If the flag contains '=', it means we've reached its value, so delegate autocompletion to it.
            if '=' in self.autocompleter.prefix:
                name = self.autocompleter.prefix.split('=', 1)[0]
                if name not in self.flags:
                    return []
                return self.flags[name].autocomplete()
            # Otherwise, autocomplete all the flags that match.
            return [flag.match() for flag in self.flags.values()]
        # Otherwise, it's an argument, so delegate autocompletion to it.
        self.argument_index = 0
        for n, word in enumerate(self.autocompleter.words):
            if n == self.autocompleter.index:
                break
            if not word.startswith('-'):
                self.argument_index += 1
        self.argument_index -= 2 # Don't count the command and subcommand.
        if self.argument_index >= len(self.arguments):
            return []
        return self.arguments[self.argument_index].autocomplete()


class Flag(object):
    
    def __init__(self, subcommand, config):
        self.subcommand = subcommand
        if '=' in config:
            self.name, self.value = config.split('=', 1)
        else:
            self.name, self.value = config, None

    def autocomplete(self):
        completer = completers.get(self.value.strip('<>'))
        if not completer:
            return []
        # Flag values are autocompleted separately, so discard the '--flag=' prefix.
        self.subcommand.autocompleter.prefix = self.subcommand.autocompleter.prefix[len(self.name)+1:]
        return completer(self, self.subcommand.autocompleter.prefix)

    def match(self):
        # If the flag doesn't start with the prefix there's no game.
        if not self.name.startswith(self.subcommand.autocompleter.prefix):
            return None
        # Otherwise, check that the flag hasn't appeared already.
        for word in self.subcommand.autocompleter.words:
            if not word.startswith('-'):
                continue
            # Flags followed by values are stripped so that only their name is considered.
            if '=' in word:
                word = word.split('=', 1)[0]
            if self.name == word:
                return None
        if self.value:
            self.subcommand.autocompleter.compopt.append('nospace') # Don't put a space after '='.
            return self.name + '='
        return self.name


class Argument(object):
    
    def __init__(self, subcommand, config):
        self.subcommand = subcommand
        self.name       = config

    def autocomplete(self):
        completer = completers.get(self.name.strip('<>'))
        if not completer:
            return []
        return completer(self, self.subcommand.autocompleter.prefix)


def complete_value(arg, prefix):
    return []
completers['value'] = complete_value


def complete_path(arg, prefix):
    arg.subcommand.autocompleter.compopt.append('filenames') # Display paths from the last slash on.
    directory, prefix = os.path.split(prefix)
    return [os.path.join(directory, entry) for entry in os.listdir(directory or '.') if entry.startswith(prefix)]
completers['path'] = complete_path


def echo(message, *args):
    # Anything printed to stdout is interpreted as autocompletion options, so print messages to stderr.
    sys.stderr.write(os.linesep + message % args + os.linesep)
    sys.stderr.flush()


def import_module(path):
    # There's no cross version method to import a module from path, so do it manually.
    path = os.path.abspath(path)
    file = os.path.basename(path)
    name = os.path.splitext(file)[0]
    with open(path) as reader:
        data = reader.read()
    code   = compile(data, file, 'exec')
    module = types.ModuleType(name)
    module.__file__ = path
    module.__name__ = name
    exec(code, vars(module))
    return module


def split(line):
    # shlex doesn't like unclosed quotes, so if that's the case we close them ourselves.
    try:
        return shlex.split(line)
    except ValueError:
        pass
    # Try closing with ".
    try:
        return shlex.split(line + '"')
    except ValueError:
        pass
    # Try closing with '.
    try:
        return shlex.split(line + "'")
    except ValueError:
        pass
    raise ValueError('invalid line: %r' % text)


def main(argv):
    if len(argv) != 5:
        echo('USAGE: %s <config-path> <line> <cursor> <index>' % argv[0])
        return +1
    try:
        autocompleter = Autocompleter(
            config_path = argv[1],
            line        = argv[2],
            cursor      = int(argv[3]),
            index       = int(argv[4]),
        )
        options = autocompleter.autocomplete()
        print(','.join(autocompleter.compopt))
        print(os.linesep.join(options))
    except Exception as error:
        echo('ERROR: %s' % error)
        traceback.print_exc()
        return -1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
