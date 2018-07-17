#! /usr/bin/env python
# -*- coding:utf-8 -*-
# Authoor: Shihai.Chen
# verilog netlist recursive descent parser

import re
import sys

# Token specification
token_regexp_list = [
    ('ID',        r'[a-zA-Z](\w)*' ),
    ('L_BRACK',   r'\('            ),
    ('R_BRACK',   r'\)'            ),
    ('DOT',       r'\.'            ),
    ('COMMAR',    r','             ),
    ('SEMI',      r';'             ),
    ('NUMBER',    r'\d(\.\d+)*'    ),
    ('NEWLINE',   r'\n'            ),
    ('SKIP',      r'[ \t]+'        ),
    ('COMMENT_L', r'/\*(.|\n)*\*\/'),
    ('COMMENT_S', r'\/\/.*'        ),
    ('MISMATCH',  r'.'             )
]
keywork_list = ['module','input','output','inout','endmodule','assign','wire']
def gen_token(token_regexp_list,chars):
    patterns_regexp = '|'.join('(?P<%s>%s)' % pats for pats in token_regexp_list)
    compile_pat = re.compile(patterns_regexp)
    line_num = 1
    line_column_start = 1
    for match_list in re.finditer(compile_pat,chars):
        token_type = match_list.lastgroup
        match_result = match_list.group(token_type)
        if token_type.find('COMMENT') != -1 or token_type == 'SKIP':
            pass
        elif token_type == 'NEWLINE':
            line_num += 1
            line_column_start = match_list.end(token_type)
        elif token_type == 'MISMATCH':
            print '>>> Error: Mismatch Chars \'%s\'in Line %d' % (match_result,line_num)
        else:
            column_num = match_list.start(token_type) - line_column_start + 1
            if token_type == 'ID' and match_result in keywork_list:
                token_type = match_result
            yield (token_type,match_result,line_num,column_num)

master_pat = re.compile('|'.join([NUM, PLUS, MINUS, TIMES,
                                  DIVIDE, LPAREN, RPAREN, WS]))

# Tokenizer
Token = collections.namedtuple('Token', ['type', 'value'])


def generate_tokens(text):
    scanner = master_pat.scanner(text)
    for m in iter(scanner.match, None):
        tok = Token(m.lastgroup, m.group())
        if tok.type != 'WS':
            yield tok


# Parser
class ExpressionEvaluator:
    '''
    Implementation of a recursive descent parser.   Each method
    implements a single grammar rule.  Use the ._accept() method
    to test and accept the current lookahead token.  Use the ._expect()
    method to exactly match and discard the next token on on the input
    (or raise a SyntaxError if it doesn't match).
    '''

    def parse(self, text):
        self.tokens = generate_tokens(text)
        self.tok = None  # Last symbol consumed
        self.nexttok = None  # Next symbol tokenized
        self._advance()  # Load first lookahead token
        return self.expr()

    def _advance(self):
        'Advance one token ahead'
        self.tok, self.nexttok = self.nexttok, next(self.tokens, None)

    def _accept(self, toktype):
        'Test and consume the next token if it matches toktype'
        if self.nexttok and self.nexttok.type == toktype:
            self._advance()
            return True
        else:
            return False

    def _expect(self, toktype):
        'Consume next token if it matches toktype or raise SyntaxError'
        if not self._accept(toktype):
            raise SyntaxError('Expected ' + toktype)

    # Grammar rules follow

    def expr(self):
        "expression ::= term { ('+'|'-') term }*"

        exprval = self.term()
        while self._accept('PLUS') or self._accept('MINUS'):
            op = self.tok.type
            right = self.term()
            if op == 'PLUS':
                exprval += right
            elif op == 'MINUS':
                exprval -= right
        return exprval

    def term(self):
        "term ::= factor { ('*'|'/') factor }*"

        termval = self.factor()
        while self._accept('TIMES') or self._accept('DIVIDE'):
            op = self.tok.type
            right = self.factor()
            if op == 'TIMES':
                termval *= right
            elif op == 'DIVIDE':
                termval /= right
        return termval

    def factor(self):
        "factor ::= NUM | ( expr )"

        if self._accept('NUM'):
            return int(self.tok.value)
        elif self._accept('LPAREN'):
            exprval = self.expr()
            self._expect('RPAREN')
            return exprval
        else:
            raise SyntaxError('Expected NUMBER or LPAREN')


if __name__ == '__main__':
    e = ExpressionEvaluator()
    print(e.parse('2'))
    print(e.parse('2 + 3'))
    print(e.parse('2 + 3 * 4'))
    print(e.parse('2 + (3 + 4) * 5'))


# Example of building trees

class ExpressionTreeBuilder(ExpressionEvaluator):
    def expr(self):
        "expression ::= term { ('+'|'-') term }"

        exprval = self.term()
        while self._accept('PLUS') or self._accept('MINUS'):
            op = self.tok.type
            right = self.term()
            if op == 'PLUS':
                exprval = ('+', exprval, right)
            elif op == 'MINUS':
                exprval = ('-', exprval, right)
        return exprval

    def term(self):
        "term ::= factor { ('*'|'/') factor }"

        termval = self.factor()
        while self._accept('TIMES') or self._accept('DIVIDE'):
            op = self.tok.type
            right = self.factor()
            if op == 'TIMES':
                termval = ('*', termval, right)
            elif op == 'DIVIDE':
                termval = ('/', termval, right)
        return termval

    def factor(self):
        'factor ::= NUM | ( expr )'

        if self._accept('NUM'):
            return int(self.tok.value)
        elif self._accept('LPAREN'):
            exprval = self.expr()
            self._expect('RPAREN')
            return exprval
        else:
            raise SyntaxError('Expected NUMBER or LPAREN')


if __name__ == '__main__':
    e = ExpressionTreeBuilder()
    print(e.parse('2 + 3'))
    print(e.parse('2 + 3 * 4'))
    print(e.parse('2 + (3 + 4) * 5'))
    print(e.parse('2 + 3 + 4'))
