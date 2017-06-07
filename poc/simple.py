''':'
autocomplete()
{
  local COMMAND=\"$1\"
  eval "
  _complete_$COMMAND()
  {
    local THIS_FILE=\"\$(readlink -f \"\${BASH_SOURCE[0]}\")\"
    local CURRENT=\"\${COMP_WORDS[\$COMP_CWORD)]}\"
    COMPREPLY=( \$(python \"\$THIS_FILE\" \"\$CURRENT\") )
  }
  complete -F _complete_$COMMAND $COMMAND
  "
}
return
'''
 
import sys
 
options = 'foo', 'bar', 'foobar'
 
if __name__ == '__main__':
  cword = sys.argv[1]
  match = [word for word in options if word.startswith(cword)]
  print('\n'.join(match))
