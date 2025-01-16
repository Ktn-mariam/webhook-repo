from flask import jsonify
from flask import request
from flask import Flask
import os
from dotenv import load_dotenv
from flask_pymongo import PyMongo
from bson.json_util import dumps
from flask_cors import CORS
from datetime import datetime
import pytz

load_dotenv()

app = Flask(__name__)
CORS(app)


# Configure MongoDB connection
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise ValueError("MONGO_URI environment variable is missing!")

app.config["MONGO_URI"] = MONGO_URI
db = PyMongo(app).db


@app.route('/')
def api_root():
  return 'Flask API Running...'


# To post the events into the MongoDB database
@app.route('/reciever', methods=['POST'])
def api_gh_message():
  try:
    if request.headers['Content-Type'] == 'application/json':
      webhook = request.json
      
      request_id = None
      author = None
      action = None
      from_branch = None
      to = None
      date = None
      
      if 'pull_request' in webhook and webhook.get('action') == 'opened':
        # pull request was created
        
        pull_request = webhook.get('pull_request')
        
        request_id = webhook.get('number')
        author = pull_request.get('user').get('login')
        action = "PULL_REQUEST"
        from_branch = pull_request.get('head').get('ref')
        to_branch = pull_request.get('base').get('ref')
        timestamp = pull_request.get('base').get('repo').get('created_at')

      elif 'pull_request' in webhook and webhook.get('action') == 'closed' and webhook.get('pull_request', {}).get('merged', None) == True:
        # pull request was merged
        
        pull_request = webhook.get('pull_request')
        
        request_id = webhook.get('number')
        author = pull_request.get('merged_by').get('login')
        action = "MERGED"
        from_branch = pull_request.get('head').get('ref')
        to_branch = pull_request.get('base').get('ref')
        timestamp = pull_request.get('merged_at')
      
      elif 'commits' in webhook:
        # code was pushed
        
        ref = webhook.get('ref')
        request_id = webhook.get('head_commit').get('id')[:7]
        author = webhook.get('pusher').get('name')
        action = "PUSHED"
        from_branch = None
        to_branch = webhook.get('ref').split("refs/heads/")[1]
        timestamp = webhook.get('head_commit').get('timestamp')
        
        
      data = {
        "request_id": request_id,
        "author": author,
        "action": action,
        "from_branch": from_branch,
        "to_branch": to_branch,
        "timestamp": timestamp
      }
      
      print(data)
      
      db.repoActions.insert_one(data)
      
      return data, 200
      
    else:
      return {"error": "Invalid Content-Type. Expected application/json"}, 400
  except Exception as e:
    return jsonify({'error': f'An error occurred: {str(e)}'}), 500



# To fetch the events from the MongoDB database
@app.route('/getAction', methods=['GET'])
def api_get_action():
  try:
    documents = db.repoActions.find().sort('_id', -1)
      
    data = list(documents)
    for doc in data:
        doc['_id'] = str(doc['_id'])
    
    return jsonify(data), 200
  except Exception as e:
    return jsonify({'error': f'An error occurred: {str(e)}'}), 500


# Running the app
if __name__ == '__main__':
  app.run(host='0.0.0.0', port=5001, debug=True)