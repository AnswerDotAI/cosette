# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_core.ipynb.

# %% auto 0
__all__ = ['empty', 'models', 'text_only_models', 'models_azure', 'find_block', 'contents', 'usage', 'wrap_latex', 'Client',
           'get_stream', 'mk_openai_func', 'mk_tool_choice', 'call_func', 'mk_toolres', 'mock_tooluse', 'Chat']

# %% ../00_core.ipynb 3
from fastcore import imghdr
from fastcore.utils import *
from fastcore.meta import delegates

import inspect, typing, mimetypes, base64, json, ast
from collections import abc
from random import choices
from string import ascii_letters,digits

from msglm import mk_msg_openai as mk_msg, mk_msgs_openai as mk_msgs

from openai import types
from openai import Completion,OpenAI,NOT_GIVEN,AzureOpenAI
from openai.resources import chat
from openai.resources.chat import Completions
from openai.types.chat.chat_completion import ChatCompletion, ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from toolslm.funccall import *

try: from IPython import display
except: display=None

# %% ../00_core.ipynb 5
empty = inspect.Parameter.empty

# %% ../00_core.ipynb 7
models = 'o1-preview', 'o1-mini', 'gpt-4o', 'gpt-4-turbo', 'gpt-4', 'gpt-4-32k', 'gpt-3.5-turbo', 'gpt-3.5-turbo-instruct'

# %% ../00_core.ipynb 9
text_only_models = 'o1-preview', 'o1-mini'

# %% ../00_core.ipynb 16
def find_block(r:abc.Mapping, # The message to look in
              ):
    "Find the message in `r`."
    m = nested_idx(r, 'choices', 0)
    if not m: return m
    if hasattr(m, 'message'): return m.message
    return m.delta

# %% ../00_core.ipynb 17
def contents(r):
    "Helper to get the contents from response `r`."
    blk = find_block(r)
    if not blk: return r
    if hasattr(blk, 'content'): return getattr(blk,'content')
    return blk

# %% ../00_core.ipynb 19
@patch
def _repr_markdown_(self:ChatCompletion):
    det = '\n- '.join(f'{k}: {v}' for k,v in dict(self).items())
    res = contents(self)
    if not res: return f"- {det}"
    return f"""{contents(self)}

<details>

- {det}

</details>"""

# %% ../00_core.ipynb 22
def usage(inp=0, # Number of prompt tokens
          out=0  # Number of completion tokens
         ):
    "Slightly more concise version of `CompletionUsage`."
    return CompletionUsage(prompt_tokens=inp, completion_tokens=out, total_tokens=inp+out)

# %% ../00_core.ipynb 24
@patch
def __repr__(self:CompletionUsage): return f'In: {self.prompt_tokens}; Out: {self.completion_tokens}; Total: {self.total_tokens}'

# %% ../00_core.ipynb 26
@patch
def __add__(self:CompletionUsage, b):
    "Add together each of `input_tokens` and `output_tokens`"
    return usage(self.prompt_tokens+b.prompt_tokens, self.completion_tokens+b.completion_tokens)

# %% ../00_core.ipynb 28
def wrap_latex(text, md=True):
    "Replace OpenAI LaTeX codes with markdown-compatible ones"
    text = re.sub(r"\\\((.*?)\\\)", lambda o: f"${o.group(1)}$", text)
    res = re.sub(r"\\\[(.*?)\\\]", lambda o: f"$${o.group(1)}$$", text, flags=re.DOTALL)
    if md: res = display.Markdown(res)
    return res

# %% ../00_core.ipynb 38
class Client:
    def __init__(self, model, cli=None):
        "Basic LLM messages client."
        self.model,self.use = model,usage(0,0)
        self.text_only = model in text_only_models
        self.c = (cli or OpenAI()).chat.completions

# %% ../00_core.ipynb 40
@patch
def _r(self:Client, r:ChatCompletion):
    "Store the result of the message and accrue total usage."
    self.result = r
    if getattr(r,'usage',None): self.use += r.usage
    return r

# %% ../00_core.ipynb 42
def get_stream(r):
    for o in r:
        o = contents(o)
        if o and isinstance(o, str): yield(o)

# %% ../00_core.ipynb 43
@patch
@delegates(Completions.create)
def __call__(self:Client,
             msgs:list, # List of messages in the dialog
             sp:str='', # System prompt
             maxtok=4096, # Maximum tokens
             stream:bool=False, # Stream response?
             **kwargs):
    "Make a call to LLM."
    assert not (self.text_only and bool(sp)), "System prompts are not supported by the current model type."
    assert not (self.text_only and stream), "Streaming is not supported by the current model type."
    if 'tools' in kwargs: assert not self.text_only, "Tool use is not supported by the current model type."
    if any(c['type'] == 'image_url' for msg in msgs if isinstance(msg, dict) and isinstance(msg.get('content'), list) for c in msg['content']): assert not self.text_only, "Images are not supported by the current model type."
    if stream: kwargs['stream_options'] = {"include_usage": True}
    if sp: msgs = [mk_msg(sp, 'system')] + list(msgs)
    r = self.c.create(
        model=self.model, messages=msgs, max_completion_tokens=maxtok, stream=stream, **kwargs)
    if not stream: return self._r(r)
    else: return get_stream(map(self._r, r))

# %% ../00_core.ipynb 51
def mk_openai_func(f): return dict(type='function', function=get_schema(f, 'parameters'))

# %% ../00_core.ipynb 52
def mk_tool_choice(f): return dict(type='function', function={'name':f})

# %% ../00_core.ipynb 59
def _mk_ns(*funcs:list[callable]) -> dict[str,callable]:
    "Create a `dict` of name to function in `funcs`, to use as a namespace"
    return {f.__name__:f for f in funcs}

# %% ../00_core.ipynb 60
def call_func(fc:types.chat.chat_completion_message_tool_call.Function, # Function block from message
              ns:Optional[abc.Mapping]=None, # Namespace to search for tools, defaults to `globals()`
              obj:Optional=None # Object to search for tools
             ):
    "Call the function in the tool response `tr`, using namespace `ns`."
    if ns is None: ns=globals()
    if not isinstance(ns, abc.Mapping): ns = _mk_ns(*ns)
    func = getattr(obj, fc.name, None)
    if not func: func = ns[fc.name]
    return func(**ast.literal_eval(fc.arguments))

# %% ../00_core.ipynb 62
def mk_toolres(
    r:abc.Mapping, # Tool use request response
    ns:Optional[abc.Mapping]=None, # Namespace to search for tools
    obj:Optional=None # Class to search for tools
    ):
    "Create a `tool_result` message from response `r`."
    r = mk_msg(r)
    tcs = getattr(r, 'tool_calls', [])
    res = [r]
    for tc in (tcs or []):
        func = tc.function
        cts = str(call_func(func, ns=ns, obj=obj))
        res.append(mk_msg(str(cts), 'tool', tool_call_id=tc.id, name=func.name))
    return res

# %% ../00_core.ipynb 70
def _mock_id(): return 'call_' + ''.join(choices(ascii_letters+digits, k=24))

def mock_tooluse(name:str, # The name of the called function
                 res,  # The result of calling the function
                 **kwargs): # The arguments to the function
    ""
    id = _mock_id()
    func = dict(arguments=json.dumps(kwargs), name=name)
    tc = dict(id=id, function=func, type='function')
    req = dict(content=None, role='assistant', tool_calls=[tc])
    resp = mk_msg('' if res is None else str(res), 'tool', tool_call_id=id, name=name)
    return [req,resp]

# %% ../00_core.ipynb 74
class Chat:
    def __init__(self,
                 model:Optional[str]=None, # Model to use (leave empty if passing `cli`)
                 cli:Optional[Client]=None, # Client to use (leave empty if passing `model`)
                 sp='', # Optional system prompt
                 tools:Optional[list]=None,  # List of tools to make available
                 tool_choice:Optional[str]=None): # Forced tool choice
        "OpenAI chat client."
        assert model or cli
        self.c = (cli or Client(model))
        self.h,self.sp,self.tools,self.tool_choice = [],sp,tools,tool_choice
    
    @property
    def use(self): return self.c.use

# %% ../00_core.ipynb 76
@patch
@delegates(Completions.create)
def __call__(self:Chat,
             pr=None,  # Prompt / message
             stream:bool=False, # Stream response?
             **kwargs):
    "Add prompt `pr` to dialog and get a response"
    if isinstance(pr,str): pr = pr.strip()
    if pr: self.h.append(mk_msg(pr))
    if self.tools: kwargs['tools'] = [mk_openai_func(o) for o in self.tools]
    if self.tool_choice: kwargs['tool_choice'] = mk_tool_choice(tool_choice)
    res = self.c(self.h, sp=self.sp, stream=stream, **kwargs)
    self.h += mk_toolres(res, ns=self.tools, obj=self)
    return res

# %% ../00_core.ipynb 92
models_azure = ('gpt-4o', 'gpt-4-32k', 'gpt4-1106-preview', 'gpt-35-turbo', 'gpt-35-turbo-16k')
