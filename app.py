######################################
# author ben lawson <balawson@bu.edu> 
# Edited by: Mona Jalal (jalal@bu.edu), Baichuan Zhou (baichuan@bu.edu) and Craig Einstein <einstein@bu.edu>
######################################
# Some code adapted from 
# CodeHandBook at http://codehandbook.org/python-web-application-development-using-flask-and-mysql/
# and MaxCountryMan at https://github.com/maxcountryman/flask-login/
# and Flask Offical Tutorial at  http://flask.pocoo.org/docs/0.10/patterns/fileuploads/
# see links for further understanding
###################################################

import flask
from flask import Flask, Response, request, render_template, redirect, url_for, send_from_directory
from flaskext.mysql import MySQL
import flask.ext.login as flask_login
import datetime
# for image uploading
# from werkzeug import secure_filename
import os, base64

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

# These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'hello'
app.config['MYSQL_DATABASE_DB'] = 'PHOTOSHARE1'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

# begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT EMAIL FROM USER")
USER = cursor.fetchall()


def getUserList():
    cursor = conn.cursor()
    cursor.execute("SELECT EMAIL FROM USER")
    return cursor.fetchall()


class User(flask_login.UserMixin):
    pass


@login_manager.user_loader
def user_loader(EMAIL):
    USER = getUserList()
    if not (EMAIL) or EMAIL not in str(USER):
        return
    user = User()
    user.id = EMAIL
    return user


@login_manager.request_loader
def request_loader(request):
    USER = getUserList()
    EMAIL = request.form.get('EMAIL')
    if not (EMAIL) or EMAIL not in str(USER):
        return
    user = User()
    user.id = EMAIL
    cursor = mysql.connect().cursor()

    cursor.execute("SELECT PASSWORD FROM USER WHERE EMAIL = %s", EMAIL)
    data = cursor.fetchall()
    pwd = str(data[0][0])
    user.is_authenticated = request.form['password'] == pwd
    return user


'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''


@app.route('/login', methods=['GET', 'POST'])
def login():
    if flask.request.method == 'GET':
        return '''
			   <form action='login' method='POST'>
				<input type='text' name='EMAIL' id='EMAIL' placeholder='EMAIL'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
    # The request method is POST (page is recieving data)
    EMAIL = flask.request.form['EMAIL']
    cursor = conn.cursor()
    # check if EMAIL is registered
    if cursor.execute("SELECT PASSWORD FROM USER WHERE EMAIL=%s",EMAIL):
        data = cursor.fetchall()
        pwd = str(data[0][0])
        if flask.request.form['password'] == pwd:
            user = User()
            user.id = EMAIL
            flask_login.login_user(user)  # okay login in user
            EMAIL= EMAIL.split('@')[0]
            return render_template('hello.html', name=EMAIL, message="Login success!")  # protected is a function defined in this file

    # information did not match
    return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"


@app.route('/logout')
def logout():
    flask_login.logout_user()
    return render_template('hello.html', message='Logged out')

#go back to home page
@app.route('/backhome')
def backhome():
    if flask_login.current_user.is_anonymous:
        name=None
    else:
        name = flask_login.current_user.id
        name = name.split('@')[0]
    return render_template('hello.html', name=name)

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('unauth.html')


# you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
    return render_template('register.html', supress='True')


@app.route("/register", methods=['POST'])
def register_user():
    try:
        EMAIL = request.form.get('email')
        password = request.form.get('password')
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        dob = request.form.get('dob')
        print(dob)
        gender = request.form.get('gender')
        hometown = request.form.get('hometown')
    except:
        print(
            "couldn't find all tokens")  # this prints to shell, end USER will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('register'))
    cursor = conn.cursor()
    test = isEMAILUnique(EMAIL)
    if test:
        print(cursor.execute("INSERT INTO USER (EMAIL, PASSWORD, GENDER, HOMETOWN, FNAME, LNAME,CONTRIBUTION, DOB) VALUES (%s,%s,%s, %s,%s,%s,0, %s)",
                             (EMAIL, password, gender,  hometown, fname, lname, dob)))
        conn.commit()
        # log user in
        user = User()
        user.id = EMAIL
        flask_login.login_user(user)
        EMAIL = EMAIL.split('@')[0]
        return render_template('hello.html', name=EMAIL, message='Account Created!')
    else:
        print("couldn't find all tokens")
        return flask.redirect(flask.url_for('register'))


def getUSERPhotos(uid):
    cursor = conn.cursor()

    cursor.execute("SELECT PHOTOURL, PID, CAPTION FROM PHOTO WHERE UID = %s", uid)
    photo = cursor.fetchall()
    return render_template('ShowPhoto.html', photopath = photo)


def getUserIdFromEMAIL(EMAIL):
    cursor = conn.cursor()
    cursor.execute("SELECT UID FROM USER WHERE EMAIL =%s", EMAIL)
    user=cursor.fetchone()
    if user==None:
        return None
    else:
        return user[0]


def isEMAILUnique(EMAIL):
    # use this to check if a EMAIL has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT EMAIL  FROM USER WHERE EMAIL =%s", EMAIL):
        # this means there are greater than zero entries with that EMAIL
        return False
    else:
        return True


# end login code

@app.route('/profile')
@flask_login.login_required
def protected():
    email = flask_login.current_user.id
    # username = email.rsplit("@", 1)
    uid = getUserIdFromEMAIL(email)
    cursor = conn.cursor()
    cursor.execute("SELECT FNAME,LNAME,GENDER,EMAIL,HOMETOWN,DOB FROM USER WHERE UID=%s",uid)
    user=cursor.fetchone()
    # cursor.execute("SELECT AID FROM ALBUM WHERE UID = %s", uid)
    # albums = cursor.fetchall()
    # return render_template('hello.html', name=username[0],  message ="Here's your profile")
    return render_template('userInfo.html', user=user)

#list all the users
@app.route("/searchUsers", methods=['GET'])
@flask_login.login_required
def showusers():
    cursor = conn.cursor()
    cursor.execute("SELECT EMAIL FROM USER WHERE EMAIL not in('"+flask_login.current_user.id+"','Visitor')")
    users = cursor.fetchall()
    recolist=getRecfriends()
    uid = getUserIdFromEMAIL(flask_login.current_user.id)
    cursor.execute(
        "SELECT U.EMAIL FROM USER U,FRIENDSHIP F WHERE F.UID1=%s AND U.UID=F.UID2",uid)
    friends = cursor.fetchall()
    cursor = conn.cursor()
    cursor.execute("SELECT EMAIL FROM USER where email<>'Visitor' order by CONTRIBUTION desc limit 10")
    topusers = cursor.fetchall()
    return render_template('searchUsers.html', userlist=users,recolist=recolist,friends=friends,topusers=topusers)

#search for a user,add a friend ,delete a friend
@app.route('/searchUsers',methods=['POST'])
@flask_login.login_required
def searchu():
    try:
           search_email= request.form.get('email1')
           add_email = request.form.get('email')
           delete_email=request.form.get('deleteemail')
    except:
            print("input is blank")
            return flask.redirect(flask.url_for('searchUsers'))
    if add_email!="" and search_email=="" and delete_email=="":#add a user
        uid = getUserIdFromEMAIL(flask_login.current_user.id)
        cursor = conn.cursor()
        if getUserIdFromEMAIL(add_email)!=None:
            userid=getUserIdFromEMAIL(add_email)
            cursor.execute("SELECT COUNT(*) FROM FRIENDSHIP F WHERE F.UID1=%s AND F.UID2=%s ", (uid,userid))
            result=cursor.fetchone();
            if result[0]==0 :
                 cursor.execute("INSERT INTO FRIENDSHIP (UID1, UID2) VALUES (%s, %s)",
                           (uid,userid))
                 cursor.execute("INSERT INTO FRIENDSHIP (UID2, UID1) VALUES (%s, %s)",
                                (uid, userid))
                 conn.commit()
                 print("add friend successful")
                 return flask.redirect(flask.url_for('showusers'))
            else:
                print("already friends")
        else:
            print("user not exist")
    if search_email!="" and add_email=="" and delete_email=="":#search for a user
        cursor = conn.cursor()
        cursor.execute("SELECT FNAME,LNAME,GENDER,EMAIL,HOMETOWN,DOB FROM USER WHERE EMAIL='" + search_email+"'")
        user = cursor.fetchone()
        if user==None:
            print("user not exist")
            return flask.redirect(flask.url_for('showusers'))
        else:
            return render_template('userInfo.html', user=user)
    if search_email=="" and add_email=="" and delete_email!="":#delete a friend
        uid = getUserIdFromEMAIL(flask_login.current_user.id)
        cursor = conn.cursor()
        if getUserIdFromEMAIL(delete_email) != None:
            userid = getUserIdFromEMAIL(delete_email)
            cursor.execute("SELECT COUNT(*) FROM FRIENDSHIP F WHERE F.UID1=%s AND F.UID2=%s ", (uid, userid))
            result = cursor.fetchone();
            if result[0] >0:#user is a friend
                cursor.execute("Delete from friendship where uid1=%s and uid2= %s",(uid,userid))
                cursor.execute("Delete from friendship where uid2=%s and uid1= %s",
                               (uid, userid))
                conn.commit()
                print("delete friend successful")
                return flask.redirect(flask.url_for('showusers'))
            else:
                print("not friends")
        else:
            print("user not exist")
    else:
        print("information incorrect")
    return flask.redirect(flask.url_for('showusers'))

@app.route('/searchComments', methods=['GET'])
def search_page():
    return render_template('searchComments.html')

# search for comments
@app.route('/searchComments', methods=['POST'])
def search_comment():
    try:
        text = request.form.get('content')
    except:
        print(
            "input error")  # this prints to shell, end USER will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('searchComments'))
    if text != "":
        cursor = conn.cursor()
        str1 = "SELECT TEMP.email,TEMP.fcount FROM (SELECT u.email, u.uid, COUNT(*)as fcount FROM user u,comment c WHERE c.uid=u.uid and c.content=%s and u.email<>'Visitor' GROUP BY u.uid) AS TEMP order by TEMP.fcount desc"
        cursor.execute(str1, text)
        list = cursor.fetchall()
        return render_template('searchComments.html', users=list)
    else:
        print("no search content")
        return render_template('searchComments.html')


#recommend friends:
def getRecfriends():
    uid = getUserIdFromEMAIL(flask_login.current_user.id)
    cursor = conn.cursor()
    str1="SELECT TEMP.email FROM (SELECT u.email, u.uid, COUNT(*)as fcount FROM user u,friendship f1,friendship f2 WHERE f1.uid1=%s and f1.uid2=f2.uid1 and f2.uid2=u.uid and u.uid<>%s and u.uid not in(SELECT uid2 from friendship where uid1=%s) GROUP BY u.uid) AS TEMP order by TEMP.fcount desc limit 5"
    cursor.execute(str1,(uid,uid,uid))
    return cursor.fetchall()

def getVisitorId():
    cursor = conn.cursor()
    cursor.execute("select uid from user where email='Visitor'")
    conn.commit()
    return cursor.fetchone()[0]

#addcomment
@app.route('/Photodetail', methods=['POST'])
def add_comment():
    try:
        content = request.form.get('content')
        pid = request.form.get('pid')
    except:
        print("input is blank")  # this prints to shell, end USER will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('searchUsers'))
    if content != "" :
        if flask_login.current_user.is_anonymous==False:
            uid = getUserIdFromEMAIL(flask_login.current_user.id)
        else:
            uid= getVisitorId()
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO COMMENT (CONTENT, DOC,UID,PID) VALUES (%s, %s,%s,%s)",(content,now,uid,pid))
        conn.commit()
        return photo_detail(pid)
    else:
        print("no content")
        return photo_detail(pid)

# add a like
@app.route('/like/<photoID>')
@flask_login.login_required
def photo_like(photoID):
    uid = getUserIdFromEMAIL(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM LIKETABLE WHERE UID=%s AND PID=%s", (uid, photoID))
    if cursor.fetchone()==None:
        now = datetime.datetime.now()
        now = now.strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO LIKETABLE (UID,PID,DOC) VALUES (%s,%s,%s)", (uid, photoID, now))
        conn.commit()
    return photo_detail(photoID)

 # begin album code
def isAlbumUnique(UID, NAME):
    # use this to check if a album name has already been registered
    cursor = conn.cursor()
    if cursor.execute("SELECT AID  FROM ALBUM WHERE UID =%s AND NAME = %s", (UID, NAME)):
        # this means there are greater than zero entries with that name
        return False
    else:
        return True

@app.route('/createalbum', methods=['GET', 'POST'])
@flask_login.login_required
def create_album():
    if request.method == 'POST':
        uid = getUserIdFromEMAIL(flask_login.current_user.id)
        albumname = request.form['name']
        if albumname and isAlbumUnique(uid, albumname):
            now = datetime.datetime.now()
            now = now.strftime("%Y-%m-%d %H:%M:%S")
            print(now)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO ALBUM (NAME , UID, DOC) VALUES (%s, %s, %s)", (albumname, uid, now))
            conn.commit()
            cursor.execute("SELECT AID FROM ALBUM WHERE NAME = %s AND UID= %s", (albumname, uid))
            aid = cursor.fetchone()[0]
            return redirect(url_for('album_detail', albumID= aid))
    else:
        return render_template('createalbum.html')

@app.route('/album')
@flask_login.login_required
def albumpage():
    uid = getUserIdFromEMAIL(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT NAME,AID,DOC  FROM ALBUM WHERE UID = %s", uid)
    albumname = cursor.fetchall()
    return render_template('albums.html', names=albumname)

@app.route('/allalbums')
def allalbumspage():
    cursor = conn.cursor()
    cursor.execute("SELECT A.NAME,A.AID, U.EMAIL, A.DOC FROM ALBUM A,USER U WHERE U.UID=A.UID ")
    albums = cursor.fetchall()
    if flask_login.current_user.is_anonymous==False:
        str1="SELECT Temp.HASHTAG FROM (Select t.hashtag,count(*)as tcount from ASSOCIATE T,PHOTO P,ALBUM A,USER U WHERE T.PID=P.PID AND P.AID=A.AID AND A.UID=U.UID AND U.EMAIL=%s group by t.hashtag)as Temp order by temp.tcount desc limit 5"
        cursor.execute(str1,flask_login.current_user.id)
        tags=""
        for tag in cursor.fetchall():
            tags=tags+"'"+tag[0]+"',"
        if tags=="":
            return render_template('allalbums.html', albums=albums)
        tags=tags[0:-1]
        count=5
        picurl=[]#recommend pics url
        while count>0:
            email=flask_login.current_user.id
            str1="Select p.pid from associate t,photo p,album a,user u  where t.hashtag in ("+tags+") and t.pid=p.pid and p.aid=a.aid and a.uid=u.uid and u.email<>%s group by p.pid having count(t.hashtag)=%s"
            cursor.execute(str1,(email,count))
            tempids=""
            for pic in cursor.fetchall():
                tempids=tempids+str(pic[0])+","
            tempids=tempids[0:-1]
            #order by the tags number of pic asc
            if tempids!="":
                str2="Select p.PHOTOURL,p.PID,p.CAPTION from associate t,photo p where t.pid in("+tempids+") and t.pid=p.pid group by p.pid order by count(t.hashtag) asc"
                cursor.execute(str2)
                for pic in cursor.fetchall():
                    picurl.append(pic)
            if len(picurl)>10:#get 10 recommend pics and break from loop
                break
            count=count-1
        return render_template('allalbums.html', albums=albums,picurl=picurl)
    else:
        return render_template('allalbums.html', albums=albums)

@app.route('/album/<albumID>')
def album_detail(albumID):
    if flask_login.current_user.is_anonymous == False:
        uid =getUserIdFromEMAIL(flask_login.current_user.id)
    else:
        uid = None
    cursor = conn.cursor()
    cursor.execute("SELECT PHOTOURL, PID,CAPTION FROM PHOTO WHERE AID = %s", albumID)
    photourl = cursor.fetchall()
    cursor.execute("SELECT UID FROM ALBUM WHERE AID = %s", albumID)
    photoowner = cursor.fetchone()[0]
    if uid == photoowner:
        owner = True
    else:
        owner = False
    return render_template('ShowPhoto.html', photopath=photourl, aid=albumID, owner = owner)

@app.route('/photos/<photoID>')
def photo_detail(photoID):
    if flask_login.current_user.is_anonymous == False:
        uid =getUserIdFromEMAIL(flask_login.current_user.id)
    else:
        uid = None
    cursor = conn.cursor()
    cursor.execute("SELECT CAPTION, PHOTOURL, AID FROM PHOTO WHERE PID = %s", photoID)
    photoinfo = cursor.fetchall()[0]
    aid = photoinfo[2]
    cursor.execute("SELECT U.UID,U.EMAIL FROM ALBUM AS A, USER AS U WHERE A.UID = U.UID AND AID = %s", aid)
    res = cursor.fetchone()
    photoowner = res[0]
    owneremail = res[1]
    if uid == photoowner:
        owner = True
    else:
        owner = False
    cursor.execute(
        "SELECT C.CONTENT,U.EMAIL,C.DOC, CASE WHEN C.UID=%s THEN C.CID ELSE 0 END AS CID FROM USER U,COMMENT C WHERE U.UID=C.UID AND C.PID=%s",
        (uid, photoID))
    photocomment = cursor.fetchall()
    cursor.execute("SELECT HASHTAG FROM ASSOCIATE WHERE PID = %s ", photoID)
    tags = cursor.fetchall()
    cursor.execute("SELECT COUNT(*) FROM LIKETABLE WHERE PID=%s", photoID)
    likecount=cursor.fetchone()[0]
    cursor.execute("SELECT U.EMAIL FROM LIKETABLE L,USER U WHERE L.UID=U.UID AND L.PID=%s", photoID)
    likeusers=cursor.fetchall()
    return render_template('Photodetail.html', tags= tags, info = photoinfo, pid = photoID,clist=photocomment,likecount=likecount,likeusers=likeusers, owner= owner,aid=aid,owneremail= owneremail)

@app.route('/deletecomment/<cid>')
@flask_login.login_required
def comment_delete(cid):
    cursor = conn.cursor()
    cursor.execute("Select pid from comment WHERE CID = %s", cid)
    pid=cursor.fetchone()[0]
    cursor.execute("DELETE FROM COMMENT WHERE CID = %s", cid)
    conn.commit()
    return photo_detail(pid)

@app.route('/deletephoto/<photoID>')
@flask_login.login_required
def photo_delete(photoID):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM COMMENT WHERE PID = %s", photoID)
    conn.commit()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM PHOTO WHERE PID = %s", photoID)
    conn.commit()
    return redirect( url_for('albumpage'))

@app.route('/deletealbum/<albumID>')
@flask_login.login_required
def album_delete(albumID):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM COMMENT WHERE PID IN (SELECT PID FROM PHOTO WHERE AID = %s)", albumID)
    conn.commit()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM PHOTO WHERE AID = %s", albumID)
    conn.commit()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM ALBUM WHERE AID = %s", albumID)
    conn.commit()
    return redirect(url_for('albumpage'))

# end album code


# begin photo uploading code
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

UPLOAD_FOLDER = './uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    print(filename)
    return  send_from_directory("uploads/", filename, as_attachment = True)

@app.route('/alrename/<albumID>', methods=[ 'GET','POST'])
@flask_login.login_required
def rename_album(albumID):
    if request.method == "POST":
        try:
            newname = request.form.get('newname')
        except:
            print("input is blank")  # this prints to shell, end USER will not see this (all print statements go to shell)
            return render_template('rename.html', message = "Album name can't be blank!")
        cursor = conn.cursor()
        cursor.execute("UPDATE ALBUM SET NAME = %s WHERE AID = %s", (newname, albumID))
        conn.commit()
        return redirect(url_for('album_detail', albumID=albumID))
    else:
        return render_template('rename.html',aid=albumID)



@app.route('/upload/<aid>', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file(aid):
    if request.method == 'POST':
        imgfile = request.files['photo']
        imgname = imgfile.filename
        tags = request.form.get("tags")
        print(tags)
        tags = tags.split('#')
        if imgfile and allowed_file(imgname):
            caption = request.form.get('caption')
            photo_url = caption
            cursor = conn.cursor()
            cursor.execute("INSERT INTO PHOTO (PHOTOURL, AID, CAPTION) VALUES (%s, %s, %s)", (photo_url, aid, caption))
            conn.commit()
            cursor = conn.cursor()
            cursor.execute("SELECT PID FROM PHOTO WHERE PHOTOURL = %s", photo_url)
            pid = cursor.fetchone()[0]
            print(pid)
            photo_url = str(pid)+ "." + (imgname.rsplit('.', 1)[1])
            imgfile.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_url))
            cursor = conn.cursor()
            cursor.execute("UPDATE PHOTO SET PHOTOURL = %s WHERE PHOTOURL = %s", (photo_url, caption))
            conn.commit()
            print(tags)
            for i in range(1, len(tags)):
                cursor = conn.cursor()
                cursor.execute("SELECT HASHTAG FROM TAG WHERE HASHTAG = %s", tags[i])
                res = cursor.fetchall()
                if len(res) == 0 and tags[i] != " ":
                    cursor = conn.cursor()
                    cursor.execute("INSERT INTO TAG (HASHTAG) VALUES (%s)", (tags[i]))
                    conn.commit()
                cursor = conn.cursor()
                cursor.execute("SELECT HASHTAG FROM ASSOCIATE WHERE HASHTAG = %s AND PID = %s", (tags[i], pid))
                exi = cursor.fetchall()
                if len(exi) == 0:
                    cursor.execute("INSERT INTO ASSOCIATE (HASHTAG, PID) VALUES (%s,%s)", (tags[i], pid))
                    conn.commit()
            return redirect( url_for('album_detail', albumID = aid))

    # The method is GET so we return a  HTML form to upload the a photo.
    else:
        cursor = conn.cursor()
        cursor.execute("SELECT HASHTAG FROM ASSOCIATE GROUP BY HASHTAG ORDER BY COUNT(PID) DESC LIMIT 10")
        tags = cursor.fetchall()
        return render_template('upload.html', aid = aid, tags =tags )

# end photo uploading code

#begin tags code

@app.route('/tags')
def view_all_photos():
    cursor = conn.cursor()
    cursor.execute("SELECT HASHTAG FROM TAG ")
    tags = cursor.fetchall()
    cursor.execute("SELECT HASHTAG FROM ASSOCIATE GROUP BY HASHTAG ORDER BY COUNT(PID) DESC LIMIT 5")
    poptags = cursor.fetchall()
    return render_template('tags.html', tags = tags,poptags=poptags)

@app.route('/tag/<tagname>')
def tag_photo(tagname):
    cursor = conn.cursor()
    cursor.execute("SELECT P.PHOTOURL, P.PID,P.CAPTION FROM ASSOCIATE AS A, PHOTO AS P WHERE A.PID = P.PID AND A.HASHTAG = %s", tagname)
    photos = cursor.fetchall()
    return render_template('photobytag.html', photos =photos, tag = tagname )

@app.route('/mytags')
@flask_login.login_required
def view_my_photos():
    uid = getUserIdFromEMAIL(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT A.HASHTAG FROM ASSOCIATE AS A, PHOTO AS P, ALBUM AS AL WHERE P.AID = AL.AID AND P.PID = A.PID AND AL.UID=%s ", uid)
    tags = cursor.fetchall()
    return render_template('tags.html', tags=tags, uid = uid)

@app.route('/mytag/<tagname>')
@flask_login.login_required
def mytag_photo(tagname):
    uid = getUserIdFromEMAIL(flask_login.current_user.id)
    cursor = conn.cursor()
    cursor.execute("SELECT P.PHOTOURL, P.PID,P.CAPTION FROM ASSOCIATE AS A, PHOTO AS P, ALBUM AS AL WHERE A.PID = P.PID AND AL.UID = %s AND AL.AID = P.AID AND A.HASHTAG = %s", (uid, tagname))
    photos = cursor.fetchall()
    return render_template('photobytag.html', photos =photos, tag = tagname )

# @app.route('/populartags')
# def popular_tags():
#     cursor = conn.cursor()
#     cursor.execute("SELECT HASHTAG FROM ASSOCIATE GROUP BY HASHTAG ORDER BY COUNT(PID) DESC LIMIT 5")
#     tags = cursor.fetchall()
#     return render_template('populartags.html', tags=tags)

@app.route('/searchphoto', methods=['GET'])
def search_photo_get():
    return render_template('searchphotos.html')

@app.route('/searchphoto', methods=['POST'])
def search_photo():
    try:
        tag = request.form.get('tag')
    except:
        print("input is blank")  # this prints to shell, end USER will not see this (all print statements go to shell)
        return flask.redirect(flask.url_for('search_photo_get'))
    tag = tag.split(", ")
    length = len(tag)
    tags = ""
    for i in range(0, length):
        tags = tags + "'" + tag[i] + "',"
    tags = tags[0:-1]
    cursor = conn.cursor()
    cursor.execute("SELECT P.PHOTOURL, P.PID FROM (Select PID from ASSOCIATE where HASHTAG in (" + tags + ")  GROUP BY PID having count(HASHTAG)=%s) AS TEM , PHOTO AS P WHERE TEM.PID = P.PID ", length)
    res = cursor.fetchall()
    if len(res)== 0:
        return render_template('searchphotos.html', message = "Photo having these tags doesn't exist!")
    else:
        return render_template('searchphotores.html', photos = res)



#end tags code

# default page
@app.route("/", methods=['GET'])
def hello():
    return render_template('hello.html', message='Welcome to Photoshare')


if __name__ == "__main__":
    # this is invoked when in the shell  you run
    # $ python app.py
    app.run(port=5000, debug=True)
