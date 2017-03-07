from datetime import datetime
from flask import render_template, redirect, url_for, session, flash
from . import main
from .forms import NameForm, EditProfileForm, EditProfileAdminForm, AddSubforumForm, DeleteSubforumForm
from .. import db
from ..models import User, Role, Post, Permission, Forum
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required

@main.route('/', methods=['GET', 'POST'])
def index():
    forum_num=Forum.query.count()
    forums=Forum.query.all()
    num=1
    for forum in forums:
        forum.order=num
        num=num+1
    return render_template('index.html',forum_num=forum_num, forums=forums, Post=Post)
    
@main.route('/user/<username>')
def user(username):
    user=User.query.filter_by(username=username).first()
    if user is None:
        abort(403)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)
    
@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form=EditProfileForm()
    if form.validate_on_submit():
        current_user.name=form.name.data
        current_user.location=form.location.data
        current_user.about_me=form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data=current_user.name
    form.location.data=current_user.location
    form.about_me.data=current_user.about_me
    return render_template('edit_profile.html', form=form)
    
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user=User.query.get_or_404(id)
    form=EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email=form.email.data
        user.username=form.username.data
        user.confirmed=form.confirmed.data
        user.name=form.name.data
        user.location=form.location.data
        user.about_me=form.about_me.data
        
        new_role=form.role.data
        if new_role[:9]=='Moderator':
            user.role=Role.query.filter_by(name='Moderator').first()
            user.subforum=Forum.query.filter_by(name=new_role[13:]).first()
        else:
            user.role=Role.query.get(form.role.data)
        
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    
    if user.subforum is None:
        form.role.data = user.role.name
    else:
        form.role.data = 'Moderator of '+user.subforum.name
    
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)    
    
@main.route('/addsubforum', methods=['GET', 'POST'])
@login_required
@admin_required
def addsubforum():
    form=AddSubforumForm()
    if form.validate_on_submit():
        forum=Forum(name=form.name.data, forumname=form.forumname.data, color=form.color.data)
        db.session.add(forum)
        db.session.commit()
        flash('New subforum has been added.')
        return redirect(url_for('.index'))
    return render_template('add_subforum.html', form=form)
    
@main.route('/deletesubforum', methods=['GET', 'POST'])
@login_required
@admin_required
def deletesubforum():  
    form=DeleteSubforumForm()  
    if form.validate_on_submit():
        delforum=Forum.query.get(form.forum.data)
        for post in delforum.posts:
            db.session.delete(post)
        db.session.delete(delforum)
        db.session.commit()
        flash('The subforum has been deleted.')
        return redirect(url_for('.index'))
    return render_template('delete_subforum.html', form=form)  
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    