from fasthtml.common import *
from claudette import *
import asyncio

# Set up the app, including daisyui and tailwind for the chat component
tlink = Script(src="https://cdn.tailwindcss.com"),
dlink = Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/daisyui@4.11.1/dist/full.min.css")
app = FastHTML(hdrs=(tlink, dlink, picolink), exts='ws')

# Set up a chat model client and list of messages (https://claudette.answer.ai/)
cli = AsyncClient(models[-1])
sp = """👋 Hello! I'm your Sentiment Analysis Assistant.
I can analyze the emotional tone of any text you share with me. Simply type your text, and I'll tell you whether it's positive or negative, along with a detailed explanation of why.
Please enter the text you'd like me to analyze:
[User can type their text here]
I will respond with:
Sentiment: [POSITIVE/NEGATIVE]
Explanation: [A clear breakdown of why I classified it that way]
For example:
If you type: 'I absolutely loved the movie!'
I'll analyze: Sentiment: POSITIVE
Explanation: Strong positive words ('loved'), emphasis ('absolutely'), enthusiastic punctuation ('!')
Or if you type: 'The service was horrible and disappointing.'
I'll analyze: Sentiment: NEGATIVE
Explanation: Contains negative descriptors ('horrible', 'disappointing'), expressing clear dissatisfaction
Please share any text you'd like me to analyze! 💭"""


messages = []

# Chat message component (renders a chat bubble)
# Now with a unique ID for the content and the message
def ChatMessage(msg_idx, **kwargs):
    msg = messages[msg_idx]
    bubble_class = "chat-bubble-primary" if msg['role']=='user' else 'chat-bubble-secondary'
    chat_class = "chat-end" if msg['role']=='user' else 'chat-start'
    return Div(Div(msg['role'], cls="chat-header"),
               Div(msg['content'],
                   id=f"chat-content-{msg_idx}", # Target if updating the content
                   cls=f"chat-bubble {bubble_class}"),
               id=f"chat-message-{msg_idx}", # Target if replacing the whole message
               cls=f"chat {chat_class}", **kwargs)

# The input field for the user message. Also used to clear the
# input field after sending a message via an OOB swap
def ChatInput():
    return Input(type="text", name='msg', id='msg-input',
                 placeholder="Type a message",
                 cls="input input-bordered w-full", hx_swap_oob='true')

# New function to generate empty chat list
def EmptyChatList():
    return Div(id="chatlist", cls="chat-box h-[73vh] overflow-y-auto")

# The main screen
@app.route("/")
def get():
    # Add a container div for the buttons with flex layout
    buttons = Div(
        Button("Clear Chat",
               cls="btn btn-error",
               hx_post="/clear",
               hx_target="#chatlist",
               hx_swap="innerHTML"),
        cls="flex justify-end mb-2"
    )
    page = Body(H1('Sentiment Analysis Assistant',),
                buttons,
                Div(*[ChatMessage(msg_idx) for msg_idx, msg in enumerate(messages)],
                    id="chatlist", cls="chat-box h-[73vh] overflow-y-auto"),
                Form(Group(ChatInput(), Button("Send", cls="btn btn-primary")),
                    ws_send=True, hx_ext="ws", ws_connect="/wscon",
                    cls="flex space-x-2 mt-2"),
                cls="p-4 max-w-lg mx-auto")
    return Title('Sentiment Analysis Assistant'), page


# Add a new route to handle clearing the chat
@app.route("/clear")
def post():
    # Clear the messages list
    messages.clear()
    # Return an empty chat list
    return EmptyChatList()

@app.ws('/wscon')
async def ws(msg:str, send):
    messages.append({"role":"user", "content":msg.rstrip()})
    swap = 'beforeend'

    # Send the user message to the user (updates the UI right away)
    await send(Div(ChatMessage(len(messages)-1), hx_swap_oob=swap, id="chatlist"))

    # Send the clear input field command to the user
    await send(ChatInput())

    # Model response (streaming)
    r = await cli(messages, sp=sp, stream=True)

    # Send an empty message with the assistant response
    messages.append({"role":"assistant", "content":""})
    await send(Div(ChatMessage(len(messages)-1), hx_swap_oob=swap, id="chatlist"))

    # Fill in the message content
    async for chunk in r:
        messages[-1]["content"] += chunk
        await send(Span(chunk, id=f"chat-content-{len(messages)-1}", hx_swap_oob=swap))

serve()

