import ast,operator
from .security import ToolPolicy,validate_tool_call
OPS={ast.Add:operator.add,ast.Sub:operator.sub,ast.Mult:operator.mul,ast.Div:operator.truediv,ast.Pow:operator.pow,ast.USub:operator.neg}
def _eval(n):
 if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return n.value
 if isinstance(n,ast.BinOp) and type(n.op) in OPS:return OPS[type(n.op)](_eval(n.left),_eval(n.right))
 if isinstance(n,ast.UnaryOp) and type(n.op) in OPS:return OPS[type(n.op)](_eval(n.operand))
 raise ValueError('Only numeric arithmetic is supported')
def calculator(expression,approved=False,policy=None):
 policy=policy or ToolPolicy();validate_tool_call('calculator',expression,policy,approved)
 if len(expression)>200:raise ValueError('Expression too long')
 return _eval(ast.parse(expression,mode='eval').body)
def text_stats(text,approved=False,policy=None):
 policy=policy or ToolPolicy();validate_tool_call('text_stats',text,policy,approved)
 return {'characters':len(text),'words':len(text.split()),'lines':len(text.splitlines())}
