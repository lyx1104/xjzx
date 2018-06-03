from flask import Blueprint, render_template, session
from models import UserInfo
news_blueprint = Blueprint("news", __name__,)


@news_blueprint.route('/')
def index():

    return render_template(
        'news/index.html'
    )

@news_blueprint.route('/back_index')
def back_index():
    return render_template(
        'news/index.html'
    )