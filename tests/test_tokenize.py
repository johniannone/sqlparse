# -*- coding: utf-8 -*-

import types

import pytest

import sqlparse
from sqlparse import lexer
from sqlparse import sql, tokens as T
from sqlparse.compat import StringIO


def test_tokenize_simple():
    s = 'select * from foo;'
    stream = lexer.tokenize(s)
    assert isinstance(stream, types.GeneratorType)
    tokens = list(stream)
    assert len(tokens) == 8
    assert len(tokens[0]) == 2
    assert tokens[0] == (T.Keyword.DML, 'select')
    assert tokens[-1] == (T.Punctuation, ';')


def test_tokenize_backticks():
    s = '`foo`.`bar`'
    tokens = list(lexer.tokenize(s))
    assert len(tokens) == 3
    assert tokens[0] == (T.Name, '`foo`')


def test_tokenize_linebreaks():
    # issue1
    s = 'foo\nbar\n'
    tokens = lexer.tokenize(s)
    assert ''.join(str(x[1]) for x in tokens) == s
    s = 'foo\rbar\r'
    tokens = lexer.tokenize(s)
    assert ''.join(str(x[1]) for x in tokens) == s
    s = 'foo\r\nbar\r\n'
    tokens = lexer.tokenize(s)
    assert ''.join(str(x[1]) for x in tokens) == s
    s = 'foo\r\nbar\n'
    tokens = lexer.tokenize(s)
    assert ''.join(str(x[1]) for x in tokens) == s


def test_tokenize_inline_keywords():
    # issue 7
    s = "create created_foo"
    tokens = list(lexer.tokenize(s))
    assert len(tokens) == 3
    assert tokens[0][0] == T.Keyword.DDL
    assert tokens[2][0] == T.Name
    assert tokens[2][1] == 'created_foo'
    s = "enddate"
    tokens = list(lexer.tokenize(s))
    assert len(tokens) == 1
    assert tokens[0][0] == T.Name
    s = "join_col"
    tokens = list(lexer.tokenize(s))
    assert len(tokens) == 1
    assert tokens[0][0] == T.Name
    s = "left join_col"
    tokens = list(lexer.tokenize(s))
    assert len(tokens) == 3
    assert tokens[2][0] == T.Name
    assert tokens[2][1] == 'join_col'


def test_tokenize_negative_numbers():
    s = "values(-1)"
    tokens = list(lexer.tokenize(s))
    assert len(tokens) == 4
    assert tokens[2][0] == T.Number.Integer
    assert tokens[2][1] == '-1'


def test_token_str():
    token = sql.Token(None, 'FoO')
    assert str(token) == 'FoO'


def test_token_repr():
    token = sql.Token(T.Keyword, 'foo')
    tst = "<Keyword 'foo' at 0x"
    assert repr(token)[:len(tst)] == tst
    token = sql.Token(T.Keyword, '1234567890')
    tst = "<Keyword '123456...' at 0x"
    assert repr(token)[:len(tst)] == tst


def test_token_flatten():
    token = sql.Token(T.Keyword, 'foo')
    gen = token.flatten()
    assert isinstance(gen, types.GeneratorType)
    lgen = list(gen)
    assert lgen == [token]


def test_tokenlist_repr():
    p = sqlparse.parse('foo, bar, baz')[0]
    tst = "<IdentifierList 'foo, b...' at 0x"
    assert repr(p.tokens[0])[:len(tst)] == tst


def test_tokenlist_first():
    p = sqlparse.parse(' select foo')[0]
    first = p.token_first()
    assert first.value == 'select'
    assert p.token_first(skip_ws=False).value == ' '
    assert sql.TokenList([]).token_first() is None


def test_tokenlist_token_matching():
    t1 = sql.Token(T.Keyword, 'foo')
    t2 = sql.Token(T.Punctuation, ',')
    x = sql.TokenList([t1, t2])
    assert x.token_matching([lambda t: t.ttype is T.Keyword], 0) == t1
    assert x.token_matching([lambda t: t.ttype is T.Punctuation], 0) == t2
    assert x.token_matching([lambda t: t.ttype is T.Keyword], 1) is None


def test_stream_simple():
    stream = StringIO("SELECT 1; SELECT 2;")

    tokens = lexer.tokenize(stream)
    assert len(list(tokens)) == 9

    stream.seek(0)
    tokens = list(lexer.tokenize(stream))
    assert len(tokens) == 9

    stream.seek(0)
    tokens = list(lexer.tokenize(stream))
    assert len(tokens) == 9


def test_stream_error():
    stream = StringIO("FOOBAR{")

    tokens = list(lexer.tokenize(stream))
    assert len(tokens) == 2
    assert tokens[1][0] == T.Error


@pytest.mark.parametrize('expr', [
    'JOIN',
    'LEFT JOIN',
    'LEFT OUTER JOIN',
    'FULL OUTER JOIN',
    'NATURAL JOIN',
    'CROSS JOIN',
    'STRAIGHT JOIN',
    'INNER JOIN',
    'LEFT INNER JOIN'])
def test_parse_join(expr):
    p = sqlparse.parse('{0} foo'.format(expr))[0]
    assert len(p.tokens) == 3
    assert p.tokens[0].ttype is T.Keyword


def test_parse_endifloop():
    p = sqlparse.parse('END IF')[0]
    assert len(p.tokens) == 1
    assert p.tokens[0].ttype is T.Keyword
    p = sqlparse.parse('END   IF')[0]
    assert len(p.tokens) == 1
    p = sqlparse.parse('END\t\nIF')[0]
    assert len(p.tokens) == 1
    assert p.tokens[0].ttype is T.Keyword
    p = sqlparse.parse('END LOOP')[0]
    assert len(p.tokens) == 1
    assert p.tokens[0].ttype is T.Keyword
    p = sqlparse.parse('END  LOOP')[0]
    assert len(p.tokens) == 1
    assert p.tokens[0].ttype is T.Keyword
