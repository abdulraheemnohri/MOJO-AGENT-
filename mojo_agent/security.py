from dataclasses import dataclass
@dataclass(frozen=True)
class ToolPolicy:
 allowed_tools:frozenset[str]=frozenset({'calculator','text_stats'})
 require_approval:bool=True
 max_input_chars:int=10000
class PermissionDenied(PermissionError):pass
def validate_tool_call(name,payload,policy,approved=False):
 if name not in policy.allowed_tools:raise PermissionDenied(f'Tool not allowlisted: {name}')
 if len(payload)>policy.max_input_chars:raise PermissionDenied('Input exceeds limit')
 if policy.require_approval and not approved:raise PermissionDenied('User approval required')
