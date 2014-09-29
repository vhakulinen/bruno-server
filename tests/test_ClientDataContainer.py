import pytest

from include import env


@pytest.fixture()
def container():
    return env.ClientDataContainer()


@pytest.mark.parametrize('input, read', [('152', False), ('01234567', True)],
                         ids=['Requal', 'Read'])
def test_dbuff(container, input, read):
    container.reset_buffers()
    container.dbuff = input
    assert container.dbuff == str(input)
    assert container.dbuff_read == read
    assert container.dbuff_size == int(input)


@pytest.mark.parametrize('first, second, expected', [('0142', '52', '014252')],
                         ids=['Basic test'])
def test_dbuff_increasement(container, first, second, expected):
    container.dbuff = first
    assert container.dbuff == first
    container.dbuff += second
    assert container.dbuff == expected


@pytest.mark.parametrize('input', ['0123456789'],
                         ids=['Value over dbuff_limit'])
def test_dbuff_ValueError(container, input):
    with pytest.raises(ValueError):
        container.dbuff = input
        container.dbuff += input


@pytest.mark.parametrize('input', ['123kl'], ids=['Input with nondigits'])
def test_dbuff_TypeError(container, input):
    with pytest.raises(TypeError):
        container.dbuff = input


@pytest.mark.parametrize('input, expected', [('hey thereäö!', 'hey thereäö!'),
                         (123, '123')], ids=['Requal string', 'Integer'])
def test_cbuff(container, input, expected):
    container.cbuff = input
    assert container.cbuff == expected
    assert container.cbuff_size == len(expected)


@pytest.mark.parametrize('first, second, expected', [('äöäö', 'êas32what',
                         'äöäöêas32what')], ids=['Baisc test'])
def test_cbuff_increasement(container, first, second, expected):
    container.cbuff = first
    assert container.cbuff == first
    container.cbuff += second
    assert container.cbuff == expected


@pytest.mark.parametrize('input, expected', [('qwem', False), ('12345', True)],
                         ids=['Not read', 'Read'])
def test_cbuff_read(container, input, expected):
    container.dbuff = '00000005'
    container.cbuff = input
    assert container.cbuff_read == expected


@pytest.mark.parametrize('input, expected', [('123', 5)], ids=['Basic test'])
def test_dbuff_left(container, input, expected):
    container.dbuff = input
    assert container.dbuff_left == expected


@pytest.mark.parametrize('dbuff, input, expected', [('00000005', 'five',
                         1)], ids=['Basic test'])
def test_cbuff_left(container, dbuff, input, expected):
    container.dbuff = dbuff
    container.cbuff = input
    assert container.cbuff_left == expected


@pytest.mark.parametrize('input,expected', [(None, False), (True, True)])
def test_authenticated(container, input, expected):
    container.profile = input
    assert container.authenticated == expected
