import os
import json
import uuid

import quart
import quart_cors
from quart import request

from llama_index import GPTListIndex, SimpleWebPageReader

app = quart_cors.cors(quart.Quart(__name__), 
        allow_origin="https://chat.openai.com")

OPENAI_API_KEY = '[OPENAI_API_KEY]'
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

wiki_pages = {}

@app.post("/post-wiki-page")
async def post_wiki_page():
    request = await quart.request.get_json(force=True)
    wiki_page_url = request["wiki_page_url"]
    wiki_id, res = post_wiki(wiki_page_url)
    if res is not None:
        wiki_pages[wiki_id] = res
    else:
        return quart.Response(response=json.dumps("Not found"), status=404)
    answer = { 
        "wiki_page_id" : wiki_id
    }
    return quart.Response(response=json.dumps(answer), status=200)

@app.get("/talk-to-wiki/<string:wiki_page_id>/<string:question>")
async def get_talk_to_wiki(wiki_page_id, question):
    try:
        if wiki_page_id in wiki_pages:
            R = get_answer(wiki_pages[wiki_page_id], question)
        else:
            R = "Answer is not available"
    except:
        R = "The plugin 'Talk to Wiki page' is in error."
    return quart.Response(response=json.dumps(R), status=200)

@app.get("/logo.png")
async def plugin_logo():
    filename = 'logo.png'
    return await quart.send_file(filename, mimetype='image/png')

@app.get("/.well-known/ai-plugin.json")
async def plugin_manifest():
    host = request.headers['Host']
    with open("./.well-known/ai-plugin.json") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/json")

@app.get("/openapi.yaml")
async def openapi_spec():
    host = request.headers['Host']
    with open("openapi.yaml") as f:
        text = f.read()
        return quart.Response(text, mimetype="text/yaml")
    
def post_wiki(url):
  try:
    wiki_page_id = uuid.uuid4().hex
    wiki_page_url = url
    pages = SimpleWebPageReader(html_to_text=True).load_data([url])
    index = GPTListIndex.from_documents(pages)
    return wiki_page_id, index
  except:
    return None

def get_answer(index, question):
  query_engine = index.as_query_engine()
  res = query_engine.query(question)
  return res.response

def main():
    app.run(debug=True, host="0.0.0.0", port=5001)

if __name__ == "__main__":
    main()
