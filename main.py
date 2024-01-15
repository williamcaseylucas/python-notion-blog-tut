from datetime import datetime, timezone
import os
from typing import List 
import requests
import json
from dotenv import load_dotenv

load_dotenv()

notionToken = os.environ['NOTION_TOKEN']
databaseId = os.environ['DATABASE_ID']

headers = {
  'Authorization': "Bearer " + notionToken,
  'Content-Type': 'application/json',
  "Notion-Version": "2022-06-28"
}
payload = {"page_size": 100}

# Copy link by clicking on three dots of db
# https://www.notion.so/3c37489266964331a26ce9461822d9e4?v=512a434cef0a427a9dd67642a7faef28&pvs=4

class NotionBlog:
  def __init__(self) -> None:
    pass
  
  def get_pages(self, num_pages=None):
    url = f'https://api.notion.com/v1/databases/{databaseId}/query'
    
    get_all = num_pages is None # boolean
    page_size = 100 if get_all else num_pages
    
    # Normally max of 100, but we can use pagination techniques otherwise
    payload = {"page_size": page_size}
    
    # res = requests.post(url,json=payload, headers=headers)
    res = requests.post(url,data=json.dumps(payload), headers=headers)
    data = res.json()
    
    with open('db.json', 'w', encoding='utf8') as f:
      # json.dump() writes to a file, json.dumps() converts a dictionary to a json string
      json.dump(data,f, ensure_ascii=False, indent=4)
        
    results = data['results']
    
    # while there is more data and we want to grab more
    while data['has_more'] and get_all:
      payload = {'page_size': page_size, 'start_cursor': data['next_cursor']}
      res = requests.post(url, data=json.dumps(payload), headers=headers)
      data = res.json()
      results.extend(data['results'])
      
    return results
  
  def parse_pages(self, pages: List):
    results = []
    for page in pages:
      props = page['properties']
      
      results.append({
        "page_id" : page['id'],
        "props" : page['properties'],
        "url" : props['Url']['title'][0]['text']['content'],
        "title" : props['Title']['rich_text'][0]['text']['content'],
        "published" : datetime.fromisoformat(props['Published']['date']['start'])
      })
    return results
      
  def create_page(self, data: dict):
    create_url = 'https://api.notion.com/v1/pages'
    
    payload = {'parent': {'database_id': databaseId}, 'properties': data}
    
    res = requests.post(create_url, headers=headers, data=json.dumps(payload))
    return res
  
  def update_page(self, page_id: str, data: dict):
    url = f'https://api.notion.com/v1/pages/{page_id}'
    payload = {'properties': data}
    
    res = requests.patch(url, json=payload, headers=headers)
    print(res.status_code)

    return res

  def delete_page(self, page_id: str):
    url = f'https://api.notion.com/v1/pages/{page_id}'
    payload = {'archived': True}
    
    res = requests.patch(url, json=payload, headers=headers)
    print(res.status_code)

    return res

notion = NotionBlog()
pages = notion.get_pages()
# print url, title, published
parsed_pages = notion.parse_pages(pages)

url = 'Test url 2'
title = 'Test Title 2'
published_date = datetime.now().astimezone(timezone.utc).isoformat()
data = {
  'Url': {'title': [{
    'text': {
      'content': url
    }
  }]},
  'Title': {
    'rich_text': [{
      'text': {
        'content': title
      }
    }]
  },
  'Published': {
    'date': {
      'start': published_date,
      'end': None
    }
  }
}

notion.create_page(data=data)

page_id = parsed_pages[0]['page_id']
title = 'I just updated this title'
updated_data = {
  'Title': {
    'rich_text': [
      {
        'text': {
          'content': title
        }
      }
    ]
  }
}

notion.update_page(page_id, updated_data)

for page in parsed_pages:
  page_id = page['page_id']
  print(page_id)
  notion.delete_page(page_id)