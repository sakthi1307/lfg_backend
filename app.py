import os
from flask import Flask, json, request, jsonify, send_file
from flask_cors import CORS
from functools import wraps
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import datetime
from bson import json_util
from bson.objectid import ObjectId
import bleach

app = Flask(__name__)
CORS(app)
posts_per_page = 9
# username =urllib.parse.quote_plus(os.environ.get('MONGO_USERNAME'))
# password = urllib.parse.quote_plus(os.environ.get('MONGO_PASSWORD'))
# MONGO_URL = urllib.parse.quote_plus(os.environ.get('MONGO_URL'))

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
uri = "mongodb+srv://lfg2:zYdhtMxy6WZKBKEZ@cluster0.iugqdiu.mongodb.net/?retryWrites=true&w=majority&tls=true&tlsAllowInvalidCertificates=true"
# uri = "mongodb+srv://sthak027:bJWVRfLRJdzZRc34@cluster0.jei53fu.mongodb.net/?retryWrites=true&w=majority"
# Create a new client and connect to the server
client = MongoClient(uri, server_api=ServerApi('1'))

# basedir = os.path.abspath(os.path.dirname(__file__))
# UPLOADS_PATH = "user-uploads"
# app.config['UPLOAD_FOLDER'] = UPLOADS_PATH

# client = MongoClient('mongodb://%s:%s@%s' % (username, password,MONGO_URL))

db = client.lgf_db

def token_required_newer(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if token:

            # Here, you would check if the token is valid and belongs to a user
            # For example, you could query your MongoDB 'lazyscorer' collection for a user with this token
            # If the token is valid, you can proceed with the decorated function
            current_user = db.users.find_one({'token':token.split(" ")[1]})
            if current_user:
                return f(current_user,*args, **kwargs)
            else:
                return jsonify({'error': 'Invalid token'}), 401
            return f(current_user,*args, **kwargs)
    return decorated_function

@app.route('/register', methods=['POST'])
def register():
    username = bleach.clean(request.form['username'])
    fname= bleach.clean(request.form['name'])
    password = bleach.clean(request.form['password'])
    user_tags = [i.strip() for i in list(request.form['user_tags'].split(","))]
    about= request.form['about'] if 'about' in request.form else ""

    if username and password:
        # Hash the password using a secure hashing algorithm
        hashed_password = generate_password_hash(password)
        # Generate a unique token for the user
        token = str(uuid.uuid4())
        # Create a new user document in the 'lazyscorer' collection
        user = {'username': username, 'password': hashed_password,'fname':fname, 'token': token,'user_tags':user_tags,'about':about}

        if db.users.find_one({'username':user['username']}):
            return jsonify({'error':"user already exists with username"}),401
        db.users.insert_one(user)
        return jsonify({'Success': "sucessfully registered"}),200
    else:
        return jsonify({'error': 'Missing username or password'}), 400


@app.route('/login', methods=['POST'])
def login():
        username = bleach.clean(request.form['username'])
        password = bleach.clean(request.form['password'])
        if username and password:
            # Find the user in the 'lazyscorer' collection
            user = db.users.find_one({'username': username})
            # print(user['password'],password)
            if user and check_password_hash(user['password'],password):
                # If the password matches, return the user's token
                return jsonify({'token': user['token']}),200
            else:
                return jsonify({'error': 'Invalid email or password'}), 401
        else:
            return jsonify({'error': 'Missing email or password'}), 400



@app.route('/addUserTag',methods=['POST'])
def add_new_tags():
    tags = list(bleach.clean(request.form['tags']).replace('[','').replace(']','').split(','))
    #TODO
    try:
        db.user_tags.insert_many([{'tag':i}for i in tags])
        return jsonify({'success':'tags added'}),200
    except Exception as e:
        return jsonify({'error':"cannot add"}),400

@app.route('/getUserTags',methods=['GET'])
def getUserTags():
    try:
        tags = db.user_tags.find()
        return jsonify({'tags':json.loads(json_util.dumps(tags))}),200
    except Exception as e:
        print(e)
        return jsonify({'error':"error getting tags"}),400

@app.route('/updateUser',methods=['POST'])
@token_required_newer
def updateUser(currentUser):
    fname = request.form['fname']
    user_tags = [i.strip() for i in list(request.form['user_tags'].replace('[','').replace(']','').split(","))]
    about= request.form['about'] if 'about' in request.form else currentUser['about']
    try:
        filt = {'username':currentUser['username']}
        newvalues = { "$set": { 'fname': fname,'user_tags':user_tags,'about':about } }
        db.users.update_one(filt,newvalues)
        return jsonify({'success':'sucessfully updated'}),200
    except Exception as e:
        print("failed to update",e)
        return jsonify({'error':'coulnt update','e':e}),400


@app.route('/getUser',methods=['GET'])
@token_required_newer
def getUser(currentUser):
    # try:
    # return jsonify({'user':json.loads(json_util.dumps(currentUser))}),200
    # except:
        # return jsonify({'error':"error"}),400
    return jsonify({'user':{'username':currentUser['username'],'fname':currentUser['fname'],'user_tags':json.loads(json_util.dumps(currentUser['user_tags'])),'about':currentUser['about']}}),200
    





@app.route('/addPostTag',methods=['POST'])
def add_post_tags():
    tags = list(bleach.clean(request.form['tags']).replace('[','').replace(']','').split(','))
    #TODO
    try:
        db.post_tags.insert_many([{'tag':i}for i in tags])
        return jsonify({'success':'tags added'}),200
    except Exception as e:
        return jsonify({'error':"cannot add"}),400

@app.route('/getPostTags',methods=['GET'])
def getPostTags():
    try:
        tags = db.post_tags.find()
        return jsonify({'tags':json.loads(json_util.dumps(tags))}),200
    except Exception as e:
        print(e)
        return jsonify({'error':"error getting tags"}),400

@app.route('/newPost',methods=['POST'])
@token_required_newer
def newPost(currentUser):
    try:
        title = bleach.clean(request.form['title'])
        description = bleach.clean(request.form['description'])
        createdAt = datetime.datetime.utcnow()
        createdBy = currentUser['fname']
        author = currentUser['username']
        post_tags = [i.strip() for i in list(request.form['post_tags'].replace('[','').replace(']','').replace('"','').split(","))]
        likes = []
        post_ = {'title':title,'description':description,'createdAt':createdAt,'createdBy':createdBy,'author':author,'likes':likes,'tags':post_tags}
        db.posts.insert_one(post_)
        return jsonify({'success':'new post published'}),200 
    except Exception as e:
        print("erroe",e)
        return jsonify({'error':'cannot publish post'}),400 

@app.route('/likePost',methods=['POST'])
@token_required_newer
def likePost(currentUser):
    try:
        post_id = bleach.clean(request.form['post_id'])
        post = db.posts.find_one({'_id':ObjectId(post_id)})
        if post is None:
            return jsonify({'error':'error finding post'}),400
        likes = list(post['likes'])
        if currentUser['username'] in likes:
            return jsonify({'error':'already liked post'}),400
        db.posts.update_one({'_id':ObjectId(post_id)},{'$push':{'likes':currentUser['username']}})
        return jsonify({'success':'successfully liked a post'}),200
    except Exception as e:
        print(e)
        return jsonify({'error':'error liking post'}),400

@app.route('/getPost',methods=['POST'])
@token_required_newer
def getPost(currentUser):
    try:
        post_id = bleach.clean(request.form['post_id'])
        post = db.posts.find_one({'_id':ObjectId(post_id)})
        if '_id' not in post:
            return jsonify({'error':'error finding post'}),400
        return jsonify({'post':json.loads(json_util.dumps(post))}),200
    except Exception as e:
        return jsonify({'error':'error getting post'}),400

@app.route('/getPosts',methods=['GET'])
@token_required_newer
def getPosts(currentUser):
    try:
        currentPage = int(request.args['page'])
        totalPages = (len(list(db.posts.find()))-1)//posts_per_page+1
        posts = db.posts.find().sort('createdAt',-1).skip((currentPage-1)*posts_per_page).limit(posts_per_page)
        return jsonify({'posts':json.loads(json_util.dumps(posts)),'totalPages':totalPages}),200
    except Exception as e:
        print(e)
        return jsonify({'error':'error getting posts'}),400
@app.route('/getPostsByUser',methods=['GET'])
@token_required_newer
def getPostsByUser(currentUser):
    try:
        currentPage = int(request.args.get('page'))
        posts = db.posts.find({'author':currentUser['username']}).sort('createdAt',-1)
        totalPages = len(list(db.posts.find({'author':currentUser['username']})))//posts_per_page+1
        posts = posts.skip((currentPage-1)*posts_per_page).limit(posts_per_page)
        return jsonify({'posts':json.loads(json_util.dumps(posts)),'totalPages':totalPages}),200
    except Exception as e:
        print(e)
        return jsonify({'error':'error getting posts'}),400
        
@app.route('/queryPosts',methods=['GET'])
@token_required_newer
def queryPosts(currentUser):
    try:
        query = bleach.clean(request.args['query'])
        db.posts.create_index([('description','text'),('title','text'),('tags','text')])
        # db.posts.create_index({'title':'text','description':'text'})
        # db.posts.create_index({'description':'text'})
        currentPage = int(request.args['page'])
        posts = db.posts.find({'$text':{"$search":query}}).sort('createdAt',-1).skip((currentPage-1)*posts_per_page).limit(posts_per_page)
        temp = list(posts)
        totalPages = (len(temp)-1)//posts_per_page+1
        return jsonify({'posts':json.loads(json_util.dumps(temp)),'totalPages':1}),200
    except Exception as e:
        print(e)
        return jsonify({'error':'error getting posts'}),400
        
        
@app.route('/deletePost',methods=['POST'])
@token_required_newer
def deletePost(currentUser):
    try:
        post_id = bleach.clean(request.form['post_id'])
        post = db.posts.find_one({'_id':ObjectId(post_id)})
        if '_id' not in post:
            return jsonify({'error':'error finding post'}),400
        if post['author']!=currentUser['username']:
            return jsonify({'error':'cannot delete post'}),400
        db.posts.delete_one({'_id':ObjectId(post_id)})
        return jsonify({'success':'successfully deleted post'}),200
    except Exception as e:
        return jsonify({'error':'error deleting post'}),400

@app.route('/updatePost',methods=['POST'])
@token_required_newer
def updatePost(currentUser):
    try:
        post_id = bleach.clean(request.form['post_id'])
        post = db.posts.find_one({'_id':ObjectId(post_id)})
        if post is None:
            return jsonify({'error':'error finding post'}),400
        if post['author']!=currentUser['username']:
            return jsonify({'error':'cannot update post'}),400
        title = bleach.clean(request.form['title']) if 'title' in request.form else post['title']
        description = bleach.clean(request.form['description']) if 'description' in request.form else post['description']
        post_tags = [i.strip() for i in list(request.form['post_tags'].replace('[','').replace(']','').replace('"','').split(","))] if 'post_tags' in request.form else post['tags']
        db.posts.update_one({'_id':ObjectId(post_id)},{'$set':{'title':title,'description':description,'tags':post_tags}})
        return jsonify({'success':'successfully updated post'}),200
    except Exception as e:
        print(e)
        return jsonify({'error':'error updating post'}),400

#recommendation algorithm
@app.route('/recommend',methods=['GET'])
@token_required_newer
def recommend(currentUser):
    try:
        user_tags = currentUser['user_tags']
        totalPages = len(list(db.posts.find({'tags':{'$in':user_tags}})))
        currentPage = int(request.args.get('page'))
        posts = db.posts.find({'tags':{'$in':user_tags}}).sort('createdAt',-1).skip((currentPage-1)*posts_per_page).limit(posts_per_page)
        temp = list(posts)
        totalPages = (len(temp)-1)//posts_per_page+1
        return jsonify({'posts':json.loads(json_util.dumps(temp)),'totalPages':1}),200
    except Exception as e:
        print(e)
        return jsonify({'error':'error getting posts'}),400

