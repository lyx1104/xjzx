from flask import Blueprint, render_template, session, request, jsonify, abort, current_app

from models import UserInfo, NewsCategory, NewsInfo, db, NewsComment

news_blueprint = Blueprint("news", __name__, )


@news_blueprint.route('/')
def index():
    category_list = NewsCategory.query.all()
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None

    count_list = NewsInfo.query. \
                     filter_by(status=2). \
                     order_by(NewsInfo.click_count.desc())[0:6]

    return render_template(
        'news/index.html',
        category_list=category_list,
        user=user,
        count_list=count_list
    )


@news_blueprint.route('/newslist')
def newslist():
    page = int(request.args.get('page', '1'))
    pagination = NewsInfo.query.filter_by(status=2)
    category_id = int(request.args.get('category_id', '0'))
    if category_id:
        pagination = pagination.filter_by(category_id=category_id)
    pagination = pagination. \
        order_by(NewsInfo.update_time.desc()). \
        paginate(page, 4, False)
    news_list = pagination.items
    news_list2 = []
    for news in news_list:
        news_dict = {
            'id': news.id,
            'pic': news.pic_url,
            'title': news.title,
            'summary': news.summary,
            'user_avatar': news.user.avatar_url,
            'user_nick_name': news.user.nick_name,
            'update_time': news.update_time.strftime('%Y-%m-%d'),
            'user_id': news.user.id,
            'category_id': news.category_id
        }
        news_list2.append(news_dict)

    return jsonify(news_list=news_list2)


@news_blueprint.route('/<int:news_id>')
def detail(news_id):
    news = NewsInfo.query.get(news_id)
    if news is None:
        abort(404)
    if 'user_id' in session:
        user = UserInfo.query.get(session['user_id'])
    else:
        user = None
    news.click_count += 1
    db.session.commit()

    count_list = NewsInfo.query. \
                     filter_by(status=2). \
                     order_by(NewsInfo.clicck_count.desc())[0:6]

    return render_template(
        'news/detail.html',
        news=news,
        title='文章详情页',
        user=user,
        count_list=count_list
    )


@news_blueprint.route('/collect', methods=['POST'])
def collect():
    action = request.form.get('action', '1')
    news_id = request.form.get('news_id')
    if not all([news_id]):
        return jsonify(result=2)
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=3)
    if 'user_id' not in session:
        return jsonify(result=1)
    user = UserInfo.query.get(session['user_id'])
    if action == '1':
        if news in user.news_collect:
            return jsonify(result=4)
        user.news_collect.append(news)
    else:
        if news not in user.news_collect:
            return jsonify(result=4)
        user.news_collect.remove(news)

    db.session.commit()

    return jsonify(result=5)


@news_blueprint.route('/comment/add', methods=['POST'])
def commentadd():
    dict1 = request.form
    news_id = dict1.get('news_id')
    msg = dict1.get('msg')

    if not all([news_id, msg]):
        return jsonify(result=2)
    news = NewsInfo.query.get(news_id)
    if news is None:
        return jsonify(result=3)

    if 'user_id' not in session:
        return jsonify(result=4)
    user_id = session['user_id']

    comment = NewsComment()
    comment.news_id = int(news_id)
    comment.user_id = user_id
    comment.msg = msg
    news.comment_count += 1

    db.session.add(comment)
    db.session.commit()

    return jsonify(result=1, comment_count=news.comment_count)


@news_blueprint.route('/comment/list/<int:news_id>')
def commentlist(news_id):
    comment_list = NewsComment.query. \
        filter_by(news_id=news_id, comment_id=None). \
        order_by(NewsComment.id.desc())
    comment_list2 = []

    if 'user_id' in session:
        user_id = session['user_id']
        commentid_list = current_app.redis_client.lrange('comment%d' % user_id, 0, -1)
        commentid_list = [int(cid) for cid in commentid_list]
    else:
        commentid_list = []

    for comment in comment_list:
        is_like = 0
        if comment.id in commentid_list:
            is_like = 1
        comment_dict = {
            'avatar': comment.user.avatar_url,
            'nick_name': comment.user.nick_name,
            'msg': comment.msg,
            'create_time': comment.create_time.strftime('%Y-%m-%d %H:%M:%S'),
            'id': comment.id,
            'is_like': is_like
        }
        cback_list = []
        cbacklist2 = comment.comments.order_by(NewsComment.id.desc())
        for cback in cbacklist2:
            cback_dict = {
                'nick_name': cback.user.nick_name,
                'msg': cback.msg
            }
            cback_list.append(cback_dict)

        comment_dict['cback_list'] = cback_list

        comment_list2.append(comment_dict)
    return jsonify(comment_list=comment_list2)


@news_blueprint.route('/comment/up/<int:comment_id>', methods=['POST'])
def commentup(comment_id):
    action = int(request.form.get('action', '1'))
    if 'user_id' not in session:
        return jsonify(result=1)
    user_id = session['user_id']
    comment = NewsComment.query.get(comment_id)
    if action == 1:
        current_app.redis_client.rpush('comment%d' % user_id, comment_id)
        comment.like_count += 1
    else:
        current_app.redis_client.lrem('comment%d' % user_id, 0, comment_id)
        comment.like_count -= 1
    db.session.commit()
    return jsonify(result=2, like_count=comment.like_count)

@news_blueprint.route('/comment/back',methods=['POST'])
def commentback():
    news_id = request.form.get('news_id')
    msg = request.form.get('msg')
    comment_id = request.form.get('comment_id')
    if not all([news_id,msg,comment_id]):
        return jsonify(result=1)
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    comment = NewsComment()
    comment.news_id = int(news_id)
    comment.user_id = user_id
    comment.comment_id = comment_id
    comment.msg = msg
    db.session.add(comment)
    db.session.commit()

    return jsonify(result=3)

@news_blueprint.route('/follow',method=['POST'])
def follow():
    action = request.form.get('action','1')
    follow_user_id = request.form.get('follow_user_id')
    if not all([follow_user_id,action]):
        return jsonify(result=1)
    if 'user_id' not in session:
        return jsonify(result=2)
    user_id = session['user_id']
    user = UserInfo.query.get(user_id)
    follow_user = UserInfo.query.get(follow_user_id)
    if action == '1':
        user.follow_user.append(follow_user)
        follow_user.follow_count += 1
    else:
        user.follow_user.remove(follow_user)
        follow_user.follow_count -= 1
    db.session.commit()
    return jsonify(result=3,follow_count=follow_user.follow_count)