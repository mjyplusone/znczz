from flask import render_template, redirect, request, url_for, flash, current_app
from flask_login import login_user, logout_user, login_required, current_user
from . import note
from .forms import PostForm
from .. import db
from ..models import User, Role, Post, Permission, Forum

@note.route('/subforum/<int:id>', methods=['GET', 'POST'])
def subforum(id):
    subforum = Forum.query.get_or_404(id)
    form=PostForm()
    if current_user.can(Permission.WRITE_ARTICLES) and \
            form.validate_on_submit():
        post=Post(body=form.body.data, 
                  author=current_user._get_current_object(),
                  subforum=subforum)
        db.session.add(post)
        return redirect(url_for('note.subforum', id=subforum.id))
    page = request.args.get('page', 1, type=int)
    pagination = Post.query.filter_by(subforum=subforum).order_by(Post.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('note/subforum.html', form=form, subforum=subforum, posts=posts, pagination=pagination)
    
@note.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    subforum=post.subforum
    return render_template('note/post.html', posts=[post], subforum=subforum)
    
@note.route('/edit/<int:id>',methods=['GET', 'POST'])
@login_required
def edit(id):
    post=Post.query.get_or_404(id)
    subforum=post.subforum
    if (current_user!=post.author and not current_user.can(Permission.ADMINISTER)) and \
            (subforum.name=='twelve' and not current_user.is_moderator_12()) and \
            (subforum.name=='eleven' and not current_user.is_moderator_11()):
        abort(403)
    form=PostForm()
    if form.validate_on_submit():
        post.body=form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('note.post', id=post.id))
    form.body.data=post.body
    return render_template('note/edit_post.html', form=form)
    
@note.route('/delete/<int:id>',methods=['GET', 'POST'])
@login_required
def delete(id):
    post=Post.query.get_or_404(id)
    subforum=post.subforum
    if (current_user!=post.author and not current_user.can(Permission.ADMINISTER)) and \
            (subforum.name=='twelve' and not current_user.is_moderator_12()) and \
            (subforum.name=='eleven' and not current_user.is_moderator_11()):
        abort(403)
    db.session.delete(post)
    flash('The post has been deleted.')
    return redirect(url_for('note.subforum', id=subforum.id))
    