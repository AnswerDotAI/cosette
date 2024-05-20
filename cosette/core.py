# AUTOGENERATED! DO NOT EDIT! File to edit: ../00_core.ipynb.

# %% auto 0
__all__ = ['empty', 'models', 'find_block', 'contents', 'usage', 'Client', 'call_func', 'mk_toolres', 'Chat', 'img_msg',
           'text_msg', 'mk_msg']

# %% ../00_core.ipynb 3
from fastcore import imghdr
from fastcore.utils import *
from fastcore.meta import delegates

import inspect, typing, mimetypes, base64, json
from collections import abc

from openai import types
from openai import Completion,OpenAI,NOT_GIVEN
from openai.resources import chat
from openai.types.chat.chat_completion import ChatCompletion, ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage

from toolslm.funccall import *

try: from IPython import display
except: display=None

# %% ../00_core.ipynb 5
empty = inspect.Parameter.empty

# %% ../00_core.ipynb 6
models = 'gpt-4o', 'gpt-4-turbo', 'turbo-2024-04-09', 'gpt4-1106-preview', 'gpt-35-turbo', 'gpt-35-turbo-16k', 'gpt-4-32k'

# %% ../00_core.ipynb 14
def find_block(r:abc.Mapping, # The message to look in
#                blk_type:type=TextBlock  # The type of block to find
              ):
    "Find the message in `r`."
    return nested_idx(r, 'choices', 0, 'message')

# %% ../00_core.ipynb 15
def contents(r):
    "Helper to get the contents from Claude response `r`."
    blk = find_block(r)
    cts = getattr(blk,'content',None)
    return cts if cts else blk

# %% ../00_core.ipynb 17
@patch
def _repr_markdown_(self:ChatCompletion):
    det = '\n- '.join(f'{k}: {v}' for k,v in dict(self).items())
    return f"""{contents(self)}

<details>

- {det}

</details>"""

# %% ../00_core.ipynb 20
def usage(inp=0, # Number of prompt tokens
          out=0  # Number of completion tokens
         ):
    "Slightly more concise version of `CompletionUsage`."
    return CompletionUsage(prompt_tokens=inp, completion_tokens=out, total_tokens=inp+out)

# %% ../00_core.ipynb 22
@patch
def __repr__(self:CompletionUsage): return f'In: {self.prompt_tokens}; Out: {self.completion_tokens}; Total: {self.total_tokens}'

# %% ../00_core.ipynb 24
@patch
def __add__(self:CompletionUsage, b):
    "Add together each of `input_tokens` and `output_tokens`"
    return usage(self.prompt_tokens+b.prompt_tokens, self.completion_tokens+b.completion_tokens)

# %% ../00_core.ipynb 32
class Client:
    def __init__(self, model, cli=None):
        "Basic LLM messages client."
        self.model,self.use = model,usage(0,0)
        self.c = (cli or OpenAI())

# %% ../00_core.ipynb 34
@patch
def _r(self:Client, r:ChatCompletion):
    "Store the result of the message and accrue total usage."
    self.result = r
    if getattr(r,'usage',None): self.use += r.usage
    return r

# %% ../00_core.ipynb 36
@patch
@delegates(chat.completions.Completions.create)
def __call__(self:Client,
             msgs:list, # List of messages in the dialog
             sp:str='', # System prompt
             maxtok=4096, # Maximum tokens
             stream:bool=False, # Stream response?
             **kwargs):
    "Make a call to LLM."
    if stream: kwargs['stream_options'] = {"include_usage": True}
    if sp: msgs = [mk_msg(sp, 'system')] + list(msgs)
    r = self.c.chat.completions.create(
        model=self.model, messages=msgs, max_tokens=maxtok, stream=stream, **kwargs)
    if not stream: return self._r(r)
    else: return map(self._r, r)

# %% ../00_core.ipynb 51
def _mk_ns(*funcs:list[callable]) -> dict[str,callable]:
    "Create a `dict` of name to function in `funcs`, to use as a namespace"
    return {f.__name__:f for f in funcs}

# %% ../00_core.ipynb 52
def call_func(fc:types.chat.chat_completion_message_tool_call.Function, # Function block from message
              ns:Optional[abc.Mapping]=None, # Namespace to search for tools, defaults to `globals()`
              obj:Optional=None # Object to search for tools
             ):
    "Call the function in the tool response `tr`, using namespace `ns`."
    if ns is None: ns=globals()
    if not isinstance(ns, abc.Mapping): ns = _mk_ns(*ns)
    func = getattr(obj, fc.name, None)
    if not func: func = ns[fc.name]
    return func(**json.loads(fc.arguments))

# %% ../00_core.ipynb 57
def mk_toolres(
    r:abc.Mapping, # Tool use request response from Claude
    ns:Optional[abc.Mapping]=None, # Namespace to search for tools
    obj:Optional=None # Class to search for tools
    ):
    "Create a `tool_result` message from response `r`."
    m = find_block(r)
    if not m: return r
    tcs = getattr(m, 'tool_calls', None)
    if not tcs: return r
    res = []
    for tc in tcs:
        func = tc.function
        cts = str(call_func(func, ns=ns, obj=obj))
        res.append(mk_msg(str(cts), 'tool', tool_call_id=tc.id, name=func.name))
    return res

# %% ../00_core.ipynb 67
class Chat:
    def __init__(self,
                 model:Optional[str]=None, # Model to use (leave empty if passing `cli`)
                 cli:Optional[Client]=None, # Client to use (leave empty if passing `model`)
                 sp='', # Optional system prompt
                 tools:Optional[list]=None): # List of tools to make available to Claude
        "Anthropic chat client."
        assert model or cli
        self.c = (cli or Client(model))
        self.h,self.sp,self.tools = [],sp,tools
    
    @property
    def use(self): return self.c.use

# %% ../00_core.ipynb 70
def _add_prefill(prefill, r):
    "Add `prefill` to the start of response `r`, since Claude doesn't include it otherwise"
    if not prefill: return
    blk = find_block(r)
    blk.text = prefill + blk.text

# %% ../00_core.ipynb 72
@patch
def __call__(self:Chat,
             pr,  # Prompt / message
             temp=0, # Temperature
             maxtok=4096, # Maximum tokens
             stop:Optional[list[str]]=None, # Stop sequences
             prefill='', # Optional prefill to pass to Claude as start of its response
             **kw):
    "Add prompt `pr` to dialog and get a response from Claude"
    if isinstance(pr,str): pr = pr.strip()
    self.h.append(mk_toolres(pr, ns=self.tools, obj=self))
    if self.tools: kw['tools'] = [get_schema(o) for o in self.tools]
    pref = [prefill.strip()] if prefill else []
    res = self.c(self.h+pref, sp=self.sp, temp=temp, maxtok=maxtok, stop=stop, **kw)
    _add_prefill(prefill, res)
    self.h.append(mk_msg(res, role='assistant'))
    return res

# %% ../00_core.ipynb 78
@patch
def stream(self:Chat,
           pr,  # Prompt / message
           sp='', # The system prompt
           temp=0, # Temperature
           maxtok=4096, # Maximum tokens
           stop:Optional[list[str]]=None, # Stop sequences
           prefill='', # Optional prefill to pass to Claude as start of its response
           **kw):
    "Add prompt `pr` to dialog and stream the response from Claude"
    if isinstance(pr,str): pr = pr.strip()
    self.h.append(pr)
    if prefill: yield(prefill)
    yield from self.c.stream(self.h + ([prefill.strip()] if prefill else []), sp=self.sp, temp=temp, maxtok=maxtok, stop=stop, **kw)
    _add_prefill(prefill, self.c.result)
    self.h.append(mk_msg(self.c.result, role='assistant'))

# %% ../00_core.ipynb 92
def img_msg(data:bytes)->dict:
    "Convert image `data` into an encoded `dict`"
    img = base64.b64encode(data).decode("utf-8")
    mtype = mimetypes.types_map['.'+imghdr.what(None, h=data)]
    r = dict(type="base64", media_type=mtype, data=img)
    return {"type": "image", "source": r}

# %% ../00_core.ipynb 94
def text_msg(s:str)->dict:
    "Convert `s` to a text message"
    return {"type": "text", "text": s}

# %% ../00_core.ipynb 98
def _mk_content(src):
    "Create appropriate content data structure based on type of content"
    if isinstance(src,str): return text_msg(src)
    if isinstance(src,bytes): return img_msg(src)
    return src

# %% ../00_core.ipynb 101
def mk_msg(content, # A string, list, or dict containing the contents of the message
           role='user', # Must be 'user' or 'assistant'
           **kw):
    "Helper to create a `dict` appropriate for a Claude message. `kw` are added as key/value pairs to the message"
    if hasattr(content, 'content'): content,role = content.content,content.role
    if isinstance(content, abc.Mapping): content=content['content']
    if not isinstance(content, list): content=[content]
    content = [_mk_content(o) for o in content] if content else '.'
    return dict(role=role, content=content, **kw)
