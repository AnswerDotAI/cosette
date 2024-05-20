# cosette


<!-- WARNING: THIS FILE WAS AUTOGENERATED! DO NOT EDIT! -->

## Install

Don’t even try. It’s not ready.

``` sh
pip install cosette
```

## Getting started

OpenAI’s Python SDK will automatically be installed with Cosette, if you
don’t already have it.

``` python
from cosette.core import models
```

Cosette only exports the symbols that are needed to use the library, so
you can use `import *` to import them. Alternatively, just use:

``` python
import cosette
```

…and then add the prefix `cosette.` to any usages of the module.

Cosette provides `models`, which is a list of models currently available
from the SDK.

``` python
models
```

    ('gpt-4o',
     'gpt-4-turbo',
     'turbo-2024-04-09',
     'gpt4-1106-preview',
     'gpt-35-turbo',
     'gpt-35-turbo-16k',
     'gpt-4-32k')

For these examples, we’ll use GPT-4o.

``` python
model = models[0]
```

## Chat

**Nothing under here works. It’s just copied from Claudette. I’m working
on it OK.**

The main interface to Claudia is the `Chat` class, which provides a
stateful interface to Claude:

``` python
chat = Chat(model, sp="""You are a helpful and concise assistant.""")
chat("I'm Jeremy")
```

It’s nice to meet you, Jeremy! I’m an AI assistant created by Anthropic.
I’m here to help with any questions or tasks you may have. Please let me
know if there’s anything I can assist you with.

<details>

- id: msg_01BtZSuhryCP1NpWwerwSXJt
- content: \[{‘text’: “It’s nice to meet you, Jeremy! I’m an AI
  assistant created by Anthropic. I’m here to help with any questions or
  tasks you may have. Please let me know if there’s anything I can
  assist you with.”, ‘type’: ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 19, ‘output_tokens’: 51}

</details>

``` python
r = chat("What's my name?")
r
```

Your name is Jeremy.

<details>

- id: msg_01W5zdkMprwYdN7zLNv5gZQK
- content: \[{‘text’: ‘Your name is Jeremy.’, ‘type’: ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 78, ‘output_tokens’: 8}

</details>

As you see above, displaying the results of a call in a notebook shows
just the message contents, with the other details hidden behind a
collapsible section. Alternatively you can `print` the details:

``` python
print(r)
```

    ToolsBetaMessage(id='msg_01W5zdkMprwYdN7zLNv5gZQK', content=[TextBlock(text='Your name is Jeremy.', type='text')], model='claude-3-haiku-20240307', role='assistant', stop_reason='end_turn', stop_sequence=None, type='message', usage=In: 78; Out: 8; Total: 86)

Claude supports adding an extra `assistant` message at the end, which
contains the *prefill* – i.e. the text we want Claude to assume the
response starts with. Let’s try it out:

``` python
chat("Concisely, what is the meaning of life?",
     prefill='According to Douglas Adams,')
```

According to Douglas Adams, “The answer to the ultimate question of
life, the universe, and everything is 42.”

<details>

- id: msg_01GKFGiZLu4wwrDe882a6MNx
- content: \[{‘text’: ‘According to Douglas Adams, “The answer to the
  ultimate question of life, the universe, and everything is 42.”’,
  ‘type’: ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 106, ‘output_tokens’: 23}

</details>

Instead of calling `Chat` directly, you can use `Chat.stream` to stream
the results as soon as they arrive (although you will only see the
gradual generation if you execute the notebook yourself, of course!)

``` python
for o in chat.stream("Concisely, what book was that in?", prefill='It was in'):
    print(o, end='')
```

    It was in The Hitchhiker's Guide to the Galaxy.

## Tool use

[Tool use](https://docs.anthropic.com/claude/docs/tool-use) lets Claude
use external tools.

We use [docments](https://fastcore.fast.ai/docments.html) to make
defining Python functions as ergonomic as possible. Each parameter (and
the return value) should have a type, and a docments comment with the
description of what it is. As an example we’ll write a simple function
that adds numbers together, and will tell us when it’s being called:

``` python
def sums(
    a:int,  # First thing to sum
    b:int=1 # Second thing to sum
) -> int: # The sum of the inputs
    "Adds a + b."
    print(f"Finding the sum of {a} and {b}")
    return a + b
```

Sometimes Claude will say something like “according to the `sums` tool
the answer is” – generally we’d rather it just tells the user the
answer, so we can use a system prompt to help with this:

``` python
sp = "Never mention what tools you use."
```

We’ll get Claude to add up some long numbers:

``` python
a,b = 604542,6458932
pr = f"What is {a}+{b}?"
pr
```

    'What is 604542+6458932?'

To use tools, pass a list of them to `Chat`:

``` python
chat = Chat(model, sp=sp, tools=[sums])
```

Now when we call that with our prompt, Claude doesn’t return the answer,
but instead returns a `tool_use` message, which means we have to call
the named tool with the provided parameters:

``` python
r = chat(pr)
r
```

ToolUseBlock(id=‘toolu_01JgEPbVF5JiwehJPWzFMLse’, input={‘a’: 604542,
‘b’: 6458932}, name=‘sums’, type=‘tool_use’)

<details>

- id: msg_01LAipBzuv5bB9QezDXgJY41
- content: \[{‘id’: ‘toolu_01JgEPbVF5JiwehJPWzFMLse’, ‘input’: {‘a’:
  604542, ‘b’: 6458932}, ‘name’: ‘sums’, ‘type’: ‘tool_use’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: tool_use
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 398, ‘output_tokens’: 72}

</details>

Cosette handles all that for us – we just have to pass along the
message, and it all happens automatically:

``` python
chat(r)
```

    Finding the sum of 604542 and 6458932

The sum of 604542 and 6458932 is 7063474.

<details>

- id: msg_01WX3khUpmrdG8F1e9yz6nmW
- content: \[{‘text’: ‘The sum of 604542 and 6458932 is 7063474.’,
  ‘type’: ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 485, ‘output_tokens’: 23}

</details>

You can see how many tokens have been used at any time by checking the
`use` property. Note that (as of May 2024) tool use in Claude uses a
*lot* of tokens, since it automatically adds a large system prompt.

``` python
chat.use
```

    In: 923; Out: 95; Total: 1018

We can do everything needed to use tools in a single step, by using
`Chat.toolloop`. This can even call multiple tools as needed solve a
problem. For example, let’s define a tool to handle multiplication:

``` python
def mults(
    a:int,  # First thing to multiply
    b:int=1 # Second thing to multiply
) -> int: # The product of the inputs
    "Multiplies a * b."
    print(f"Finding the product of {a} and {b}")
    return a * b
```

Now with a single call we can calculate `(a+b)*2` – by passing
`show_trace` we can see each response from Claude in the process:

``` python
chat = Chat(model, sp=sp, tools=[sums,mults])
pr = f'Calculate ({a}+{b})*2'
pr
```

    'Calculate (604542+6458932)*2'

``` python
chat.toolloop(pr, show_trace=True)
```

    ToolsBetaMessage(id='msg_017rs6nqX3cFgnoTgb6x7frj', content=[TextBlock(text="Okay, let's calculate that step-by-step:", type='text'), ToolUseBlock(id='toolu_0121PUsNMncXygjWoRn9rxJC', input={'a': 604542, 'b': 6458932}, name='sums', type='tool_use')], model='claude-3-haiku-20240307', role='assistant', stop_reason='tool_use', stop_sequence=None, type='message', usage=In: 528; Out: 86; Total: 614)
    Finding the sum of 604542 and 6458932
    ToolsBetaMessage(id='msg_01BtiycbFqt6jRRxHaKZd63U', content=[TextBlock(text="Now we'll multiply that sum by 2:", type='text'), ToolUseBlock(id='toolu_011EeL6GwgSYx7Y6D89Jk1QB', input={'a': 7063474, 'b': 2}, name='mults', type='tool_use')], model='claude-3-haiku-20240307', role='assistant', stop_reason='tool_use', stop_sequence=None, type='message', usage=In: 628; Out: 83; Total: 711)
    Finding the product of 7063474 and 2
    ToolsBetaMessage(id='msg_01HS7iZubJZWmDLnusWMrZuS', content=[TextBlock(text='So the final result is 14,126,948.', type='text')], model='claude-3-haiku-20240307', role='assistant', stop_reason='end_turn', stop_sequence=None, type='message', usage=In: 725; Out: 16; Total: 741)

So the final result is 14,126,948.

<details>

- id: msg_01HS7iZubJZWmDLnusWMrZuS
- content: \[{‘text’: ‘So the final result is 14,126,948.’, ‘type’:
  ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 725, ‘output_tokens’: 16}

</details>

## Images

Claude can handle image data as well. As everyone knows, when testing
image APIs you have to use a cute puppy.

``` python
fn = Path('samples/puppy.jpg')
display.Image(filename=fn, width=200)
```

![](index_files/figure-commonmark/cell-20-output-1.jpeg)

We create a `Chat` object as before:

``` python
chat = Chat(model)
```

Claudia expects images as a list of bytes, so we read in the file:

``` python
img = fn.read_bytes()
```

Prompts to Claudia can be lists, containing text, images, or both, eg:

``` python
chat([img, "In brief, what color flowers are in this image?"])
```

The image contains purple or lavender-colored flowers, which appear to
be daisies or a similar type of flower.

<details>

- id: msg_017i7Su5rfcdcz3FmiEQ9CvD
- content: \[{‘text’: ‘The image contains purple or lavender-colored
  flowers, which appear to be daisies or a similar type of flower.’,
  ‘type’: ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 185, ‘output_tokens’: 28}

</details>

The image is included as input tokens.

``` python
chat.use
```

    In: 185; Out: 28; Total: 213

Alternatively, Cosette supports creating a multi-stage chat with
separate image and text prompts. For instance, you can pass just the
image as the initial prompt (in which case Claude will make some general
comments about what it sees), and then follow up with questions in
additional prompts:

``` python
chat = Chat(model)
chat(img)
```

The image shows a cute puppy lying in the grass. The puppy appears to be
a Cavalier King Charles Spaniel, with a fluffy brown and white coat. The
puppy is looking directly at the camera with a friendly, curious
expression. In the background, there are some purple flowers, adding a
nice natural setting to the scene. The image captures the adorable and
playful nature of this young pup.

<details>

- id: msg_01K36rQXar93QVV5PzzaAoPr
- content: \[{‘text’: ‘The image shows a cute puppy lying in the grass.
  The puppy appears to be a Cavalier King Charles Spaniel, with a fluffy
  brown and white coat. The puppy is looking directly at the camera with
  a friendly, curious expression. In the background, there are some
  purple flowers, adding a nice natural setting to the scene. The image
  captures the adorable and playful nature of this young pup.’, ‘type’:
  ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 173, ‘output_tokens’: 91}

</details>

``` python
chat('What direction is the puppy facing?')
```

The puppy in the image is facing towards the camera, looking directly at
the viewer.

<details>

- id: msg_013CqCFmEzPvc6mW5kAP8fki
- content: \[{‘text’: ‘The puppy in the image is facing towards the
  camera, looking directly at the viewer.’, ‘type’: ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 275, ‘output_tokens’: 21}

</details>

``` python
chat('What color is it?')
```

The puppy in the image has a brown and white coat color. It appears to
be a Cavalier King Charles Spaniel breed, with the characteristic long,
silky fur in those colors.

<details>

- id: msg_01XfDZDRyaNMW58TVJ9znXjR
- content: \[{‘text’: ‘The puppy in the image has a brown and white coat
  color. It appears to be a Cavalier King Charles Spaniel breed, with
  the characteristic long, silky fur in those colors.’, ‘type’:
  ‘text’}\]
- model: claude-3-haiku-20240307
- role: assistant
- stop_reason: end_turn
- stop_sequence: None
- type: message
- usage: {‘input_tokens’: 304, ‘output_tokens’: 44}

</details>

Note that the image is passed in again for every input in the dialog, so
that number of input tokens increases quickly with this kind of chat.

``` python
chat.use
```

    In: 752; Out: 156; Total: 908
