import sys

import pytest
from Cheetah.NameMapper import NotFound

from galaxy.util.template import fill_template

SIMPLE_TEMPLATE = """#for item in $a_list:
    echo $item
    #end for
"""
FILLED_SIMPLE_TEMPLATE = """    echo 1
    echo 2
"""
LIST_COMPREHENSION_TEMPLATE = """#for $i in [1]:
#set $v = "".join([str(_) for _ in [1] if _ == $i])
echo $v
#end for
"""


def test_fill_simple_template():
    template_str = str(fill_template(SIMPLE_TEMPLATE, {'a_list': [1, 2]}))
    assert template_str == FILLED_SIMPLE_TEMPLATE


def test_fill_list_comprehension_template():
    if sys.version_info.major > 2:
        with pytest.raises(NotFound):
            str(fill_template(LIST_COMPREHENSION_TEMPLATE, retry=0))
    else:
        template_str = str(fill_template(LIST_COMPREHENSION_TEMPLATE, retry=0))
        assert template_str == 'echo 1\n'


def test_fill_list_comprehension_template_2():
    template_str = str(fill_template(LIST_COMPREHENSION_TEMPLATE, retry=1))
    assert template_str == 'echo 1\n'
