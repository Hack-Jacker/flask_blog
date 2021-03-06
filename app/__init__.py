#! /env python
# _*_ coding:utf8 _*_
# @author:Ren
# @time:2017/8/30 21:44

import jinja2
from flask import Flask, redirect, url_for, render_template, g
from flask_principal import identity_loaded, RoleNeed, UserNeed
from flask_login import current_user

from .config import *
from .models import db
# 扩展
from .extensions import bcrypt, login_manager, principal, cache,moment
# blog视图函数
from .blog import *


# 默认情况下 Flask的jinja_loader将会从全局加载template，这将会导致多个蓝图
# 模板命名的冲突，导致加载模板出现混乱，该类继承Flask，通过将Flask自身的
# jinja_loader重写成一个ChoicLoader来选择jinja_loader，如果注册了蓝图，该
# 类实例将首先从蓝图目录加载template而不是全局，所以不会出现命名混乱的情况
# 但这将会导致调用模板必须添加蓝图前缀，但谁说这不是我的本意呢？


class App(Flask):
    """
    In general jinja_loader will load the template form global path
    If registered the blueprint
    jinja_loader will load the templates form the blueprint's path
    """

    def __init__(self):
        Flask.__init__(self, __name__)
        self.jinja_loader = jinja2.ChoiceLoader([self.jinja_loader, jinja2.PrefixLoader({}, delimiter=".")])

    def create_global_jinja_loader(self):
        return self.jinja_loader

    def register_blueprint(self, bp):
        Flask.register_blueprint(self, bp)
        self.jinja_loader.loaders[1].mapping[bp.name] = bp.jinja_loader


# 创建App实例
def create_app(object_name=DevConfig):
    app = App()
    # Get the config form object od Devconfig
    app.config.from_object(object_name)
    # Init db object
    db.init_app(app)
    # Init flask_login
    login_manager.init_app(app)
    # Init flask_principal
    principal.init_app(app)
    # Init moment
    moment.init_app(app)
    # Init the bcrypt via app object      
    # bcrypt.init_app(app)
    # Init the cache via app object
    cache.init_app(app, config={'CACHE_TYPE': 'simple'})

    @identity_loaded.connect_via(app)
    def on_identity_loaded(sender, identity):
        """Change the role via add the need object into Role
        Need the access the app object
        """
        identity.user = current_user

        # add the userneed to the identity user object
        if hasattr(current_user, 'id'):
            identity.provides.add(UserNeed(current_user.id))
        # Add each role to the identity user objcet
        if hasattr(current_user, 'roles'):
            for role in current_user.roles:
                identity.provides.add(RoleNeed(role.role))

    @app.route('/')
    def index():
        return redirect(url_for('blog.index'))

    return app

app = create_app(DevConfig)
# Register the blog Blueprint into app object
app.register_blueprint(blog_blueprint)
app.register_blueprint(account_blueprint)
app.register_blueprint(admin_blueprint)
app.register_blueprint(upload_blueprint)
app.register_blueprint(api_blueprint)


@app.before_request
def before_request():
    g.user = current_user
    g.db = db


@app.after_request
def after_request(response):
    return response


@app.teardown_request
def teardown_request(excetption):
    pass


@app.errorhandler(404)
def page_not_found(e):
    return render_template('blog.404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('blog.500.html'), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
