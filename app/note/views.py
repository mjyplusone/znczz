from flask import render_template, redirect, request, url_for, flash, current_app, make_response
from flask_login import login_user, logout_user, login_required, current_user
from . import note
from .forms import PostForm, CommentForm, SetModeratorForm
from .. import db
from ..models import User, Role, Post, Permission, Forum, Follow, Comment
from ..decorators import admin_required, permission_required

@note.route('/subforum/<int:id>', methods=['GET', 'POST'])
def subforum(id):
    subforum = Forum.query.get_or_404(id)
    form1=PostForm()
    form2=SetModeratorForm()
    if current_user.can(Permission.WRITE_ARTICLES) and form1.validate_on_submit():
        post=Post(body=form1.body.data, 
                  author=current_user._get_current_object(),
                  subforum=subforum)
        db.session.add(post)
        return redirect(url_for('note.subforum', id=subforum.id))
    # Enter the forum and set the moderator
    if current_user.is_administrator() and form2.validate_on_submit():
        if form2.setmoderator.data != 0:
            user=User.query.get(form2.setmoderator.data)
            user.subforum=subforum
            user.role=Role.query.filter_by(name='Moderator').first()
            db.session.add(user)            
        elif subforum.users != None:
            user=subforum.users
            user.role=Role.query.filter_by(name='User').first()
            user.subforum=None
            db.session.add(user)
        return redirect(url_for('note.subforum', id=subforum.id))
    page = request.args.get('page', 1, type=int)
    query = Post.query.filter_by(subforum=subforum).order_by(Post.timestamp.desc())
    show_followed=False
    if current_user.is_authenticated:
        show_followed=bool(request.cookies.get('show_followed', ''))
    if show_followed:
        # query=current_user.followed_posts
        query=query.join(Follow, Follow.followed_id==Post.author_id).filter(Follow.follower_id==current_user.id)
    pagination = query.paginate(page, per_page=current_app.config['FLASKY_POSTS_PER_PAGE'], error_out=False)
    posts = pagination.items
    return render_template('note/subforum.html', id=id, form1=form1, form2=form2, subforum=subforum, posts=posts, pagination=pagination, show_followed=show_followed)
    
@note.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    subforum=post.subforum
    form=CommentForm()
    if form.validate_on_submit():
        comment=Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        flash('Your comment has been published. ')
        return redirect(url_for('note.post', id=post.id, page=-1))
    page=request.args.get('page', 1, type=int)
    if page==-1:
        page=(post.comments.count()-1)/current_app.config['FLASKY_COMMENTS_PER_PAGE']+1
    pagination=post.comments.order_by(Comment.timestamp.asc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    comments=pagination.items    
    return render_template('note/post.html', posts=[post], subforum=subforum, form=form, comments=comments, pagination=pagination)
    
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
    for comment in post.comments:
        db.session.delete(comment)
    db.session.delete(post)
    flash('The post has been deleted.')
    return redirect(url_for('note.subforum', id=subforum.id))
    
@note.route('/all/<int:id>')
@login_required
def show_all(id):
    resp=make_response(redirect(url_for('note.subforum', id=id)))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp

@note.route('/followed/<int:id>')
@login_required
def show_followed(id):
    resp=make_response(redirect(url_for('note.subforum', id=id)))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp

@note.route('/moderate')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate():
    page=request.args.get('page', 1, type=int)
    pagination=Comment.query.order_by(Comment.timestamp.desc()).paginate(page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'], error_out=False)
    comments=pagination.items
    return render_template('note/moderate.html', comments=comments, pagination=pagination, page=page)    
    
@note.route('/moderate/enable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=False
    db.session.add(comment)
    return redirect(url_for('note.moderate', page=request.args.get('page', 1, type=int)))
    
@note.route('/moderate/disable/<int:id>')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    comment=Comment.query.get_or_404(id)
    comment.disabled=True
    db.session.add(comment)
    return redirect(url_for('note.moderate', page=request.args.get('page', 1, type=int)))
        