import random

import qiniu

from config import Config
from models import db,UserInfo
from flask import Blueprint, make_response, session, jsonify, g, render_template
from flask import request

user_blueprint = Blueprint("user", __name__, url_prefix='/user',static_folder='static',static_url_path='/static')
from PIL import ImageFont


@user_blueprint.route('/image_yzm')
def image_yzm():
    from utils.captcha.captcha import captcha
    name, yzm, image = captcha.generate_captcha()
    session['image_yzm'] = yzm
    print(session['image_yzm'])
    response = make_response(image)
    response.mimetype = 'image/png'  # 告知浏览器媒体类型
    return response

@user_blueprint.route('/smscode')
def smscode():
    dict = request.args
    mobile = dict.get('mobile')
    image_yzm = dict.get('image_code')
    if image_yzm != session['image_yzm']:
        return jsonify(result=2)
    code = random.randint(100000,999999)
    session['smscode'] = code
    print(code)
    return jsonify(result=1,msg_code=code)

@user_blueprint.route('/register',methods=['post'])
def register():
    dict = request.form
    moblie = dict.get('mobile')
    smscode = int(dict.get('smscode'))
    password = dict.get('password')

    if smscode != session['smscode']:
        return jsonify(result=2)
    user = UserInfo.query.filter_by(mobile=moblie).first()
    print(user)
    if user:
        return jsonify(result=3)

    user =UserInfo()
    user.nick_name=moblie

    user.mobile=moblie
    user.password=password
    db.session.add(user)
    db.session.commit()
    return jsonify(result=1)

@user_blueprint.route('/login',methods=['post'])
def login():
    dict = request.form
    mobile = dict.get('mobile')
    password = dict.get('password')
    user = UserInfo.query.filter_by(mobile=mobile).first()
    if user:
        if user.check_pwd(password):
            session['user_id'] = user.id
            avatar = user.avatar

            nick_name = user.nick_name
            # print(user.avatar)
            # print(avatar)
            # print(g.user.nickname)
            return jsonify(result=1,avatar=avatar,nick_name=nick_name)
        else:
            return jsonify(result=3)
    else:
        return jsonify(result=2)
    

@user_blueprint.route('/logout',methods=['POST'])
def logout():
    session.pop('user_id')
    return jsonify(result=1)

@user_blueprint.route('/')
def index():
    user_id = session.get('user_id')
    # print(user_id)
    user = UserInfo.query.get(user_id)

    return render_template('user/user.html',
                           title='用户中心',
                           user=user,
                          )



@user_blueprint.route('/base',methods=['POST','GET'])
def base():
    user = UserInfo.query.get(session['user_id'])
    if request.method == 'GET':
        return render_template('user/user_base_info.html',user=user)
    else:
        dict = request.form
        signature = dict.get('signature')
        nick_name = dict.get('nick_name')
        gender = int(dict.get('gender'))

        user.signature = signature
        user.nick_name = nick_name
        user.gender = bool(gender)
        db.session.add(user)
        db.session.commit()

        return jsonify(result=1)

@user_blueprint.route('/pic',methods=['GET','POST'])
def pic():
    user = UserInfo.query.get(session.get('user_id'))
    if request.method == 'GET':
        return render_template('user/user_pic_info.html',user=user)
    else:
        avatar = request.files.get('avatar')
        # print(avatar)
        q = qiniu.Auth(Config.QINIU_AK,Config.QINIU_SK)
        if user.avatar == "user_pic.png":
            key = user.avatar + str(user.id)
        else:
            key = user.avatar +'1'

        data = avatar.read()
        token = q.upload_token(Config.QINIU_BUCKET)
        ret,info = qiniu.put_data(token,key,data)
        if ret is not None:
            print(ret)
        else:
            print(info)
        user.avatar=key
        db.session.add(user)
        db.session.commit()
        return jsonify(result=1,avatar_url=user.avatar_url)