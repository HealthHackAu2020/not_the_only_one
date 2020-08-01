from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
    send_file
)
from flask_login import current_user, login_required
from flask_rq import get_queue
from app.utils import db_session_add, db_session_delete
from app.admin.forms import (
    InviteUserForm,
    NewUserForm,
    EditUserForm,
    NewGroupForm,
    EditGroupForm,
    NewCategoryForm,
    EditCategoryForm,
    EditStoryForm,
)
from app.account.forms import EditCollectionForm
from app.decorators import admin_required
from app.email_helper import send_email
from app.models import EditableHTML, Role, User, Group, Story, Category, Collection, LookupValue
import os, time, datetime

admin = Blueprint('admin', __name__)


@admin.route('/')
@login_required
@admin_required
def index():
    """Admin dashboard page."""
    file = "./app/fullTweetsData.json"
    json_modified = datetime.datetime.strptime(time.ctime(os.path.getmtime(file)), "%a %b %d %H:%M:%S %Y")
    json_modified_nice = json_modified.strftime("%d %B %Y, %H:%M:%S")
    return render_template('admin/index.html', json_modified=json_modified_nice)


@admin.route('/new-user', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    """Create a new user."""
    form = NewUserForm()
    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)
        db_session_add(user)
        
        flash('User {} successfully created'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/invite-user', methods=['GET', 'POST'])
@login_required
@admin_required
def invite_user():
    """Invites a new user to create an account and set their own password."""
    form = InviteUserForm()
    if form.validate_on_submit():
        user = User()
        form.populate_obj(user)
        db_session_add(user)
        
        token = user.generate_confirmation_token()
        invite_link = url_for(
            'account.join_from_invite',
            user_id=user.id,
            token=token,
            _external=True)
        get_queue().enqueue(
            send_email,
            recipient=user.email,
            subject='You Are Invited To Join',
            template='account/email/invite',
            user=user,
            invite_link=invite_link,
        )
        form = InviteUserForm()
        flash('User {} successfully invited'.format(user.full_name()),
              'form-success')
    return render_template('admin/new_user.html', form=form)


@admin.route('/groups')
@login_required
@admin_required
def manage_groups():
    """View all user groups."""
    users = User.query.all()
    groups = Group.query.all()
    return render_template(
        'admin/manage_groups.html', users=users, groups=groups)


@admin.route('/new-group', methods=['GET', 'POST'])
@login_required
@admin_required
def new_group():
    """Create a new group."""
    form = NewGroupForm()
    if form.validate_on_submit():
        group = Group(
            name=form.name.data,
            users=form.users.data
        )
        db_session_add(group)
        
        flash('Group {} successfully created'.format(group.name),
              'form-success')
    return render_template('admin/new_group.html', form=form)


@admin.route('/group/<int:group_id>')
@admin.route('/group/<int:group_id>/info')
@login_required
@admin_required
def group_info(group_id):
    """View a group."""
    group = Group.query.filter_by(id=group_id).first()
    if group is None:
        abort(404)
    return render_template('admin/manage_group.html', group=group)
    

@admin.route('/group/<int:group_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def change_group(group_id):
    """Change a group's name."""
    group = Group.query.filter_by(id=group_id).first()
    if group is None:
        abort(404)
    form = EditGroupForm(obj=group)
    if form.validate_on_submit():
        form.populate_obj(group)
        db_session_add(group)
        
        flash('Successfully updated group {}.'.format(
            group.name), 'form-success')
    return render_template('admin/manage_group.html', group=group, form=form)


@admin.route('/group/<int:group_id>/delete')
@login_required
@admin_required
def delete_group_request(group_id):
    """Request deletion of a group's account."""
    group = Group.query.filter_by(id=group_id).first()
    if group is None:
        abort(404)
    return render_template('admin/manage_group.html', group=group)


@admin.route('/group/<int:group_id>/_delete')
@login_required
@admin_required
def delete_group(group_id):
    """Delete a group's account."""
    group = Group.query.filter_by(id=group_id).first()
    db_session_delete(group)
    
    flash('Successfully deleted group %s.' % group.name, 'success')
    return redirect(url_for('admin.manage_groups'))


@admin.route('/users')
@login_required
@admin_required
def manage_users():
    """View all registered users."""
    users = User.query.all()
    roles = Role.query.all()
    return render_template(
        'admin/manage_users.html', users=users, roles=roles)


@admin.route('/user/<int:user_id>')
@admin.route('/user/<int:user_id>/info')
@login_required
@admin_required
def user_info(user_id):
    """View a user's profile."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route(
    '/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def change_user(user_id):
    """Edit user."""
    if current_user.id == user_id:
        flash('You cannot edit your own account from the admin dashboard. Please ask '
              'another administrator to do this.', 'error')
        return redirect(url_for('admin.user_info', user_id=user_id))

    user = User.query.get(user_id)
    if user is None:
        abort(404)
    form = EditUserForm(obj=user)
    if form.validate_on_submit():
        form.populate_obj(user)
        db_session_add(user)
        
        flash('User {} successfully updated.'.format(
            user.full_name()), 'form-success')
    return render_template('admin/manage_user.html', user=user, form=form)


@admin.route('/user/<int:user_id>/delete')
@login_required
@admin_required
def delete_user_request(user_id):
    """Request deletion of a user's account."""
    user = User.query.filter_by(id=user_id).first()
    if user is None:
        abort(404)
    return render_template('admin/manage_user.html', user=user)


@admin.route('/user/<int:user_id>/_delete')
@login_required
@admin_required
def delete_user(user_id):
    """Delete a user's account."""
    if current_user.id == user_id:
        flash('You cannot delete your own account. Please ask another '
              'administrator to do this.', 'error')
    else:
        user = User.query.filter_by(id=user_id).first()
        db_session_delete(user)
        
        flash('Successfully deleted user %s.' % user.full_name(), 'success')
    return redirect(url_for('admin.manage_users'))


@admin.route('/_update_editor_contents', methods=['POST'])
@login_required
@admin_required
def update_editor_contents():
    """Update the contents of an editor."""

    edit_data = request.form.get('edit_data')
    editor_name = request.form.get('editor_name')

    editor_contents = EditableHTML.query.filter_by(editor_name=editor_name).first()
    if editor_contents is None:
        editor_contents = EditableHTML(editor_name=editor_name)
    editor_contents.value = edit_data

    db_session_add(editor_contents)
    return 'OK', 200


@admin.route('/download', methods=['GET'])
@login_required
@admin_required
def download():
  try:
    return send_file('./fullTweetsData.json', as_attachment=True, attachment_filename='fullTweetsData.json')
  except Exception as e:
    return str(e)


@admin.route('/stories')
@login_required
@admin_required
def manage_stories():
    """View all stories."""
    stories = Story.query.all()
    return render_template('admin/manage_stories.html', stories=stories)


@admin.route('/categories')
@login_required
@admin_required
def manage_categories():
    """View all categories."""
    categories = Category.query.all()
    return render_template('admin/manage_categories.html', categories=categories)


@admin.route('/collections')
@login_required
@admin_required
def manage_collections():
    """View all collections."""
    collections = Collection.query.all()
    return render_template('admin/manage_collections.html', collections=collections)

########################## Story Management ##########################

@admin.route('/story/<int:story_id>')
@admin.route('/story/<int:story_id>/info')
@login_required
@admin_required
def story_info(story_id):
    """View a story's metadata."""
    story = Story.query.filter_by(id=story_id).first()
    if story is None:
        abort(404)
    return render_template('admin/manage_story.html', story=story)


@admin.route(
    '/story/<int:story_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def change_story(story_id):
    """Edit story."""
    story = Story.query.get(story_id)
    if story is None:
        abort(404)
    form = EditStoryForm(obj=story)
    if form.validate_on_submit():
        form.populate_obj(story)
        true_value = LookupValue.query.filter_by(group="bool",value="True").first()
        story.curated = true_value
        db_session_add(story)
        
        flash('Story {} successfully updated.', 'form-success')
    return render_template('admin/manage_story.html', story=story, form=form)


@admin.route('/story/<int:story_id>/delete')
@login_required
@admin_required
def delete_story_request(story_id):
    """Request deletion of a story."""
    story = Story.query.filter_by(id=story_id).first()
    if story is None:
        abort(404)
    return render_template('admin/manage_story.html', story=story)


@admin.route('/story/<int:story_id>/_delete')
@login_required
@admin_required
def delete_story(story_id):
    """Delete a story."""
    story = Story.query.filter_by(id=story_id).first()
    db_session_delete(story)
        
    flash('Successfully deleted story', 'success')
    return redirect(url_for('admin.manage_stories'))


########################## Category Management ##########################

@admin.route('/new-category', methods=['GET', 'POST'])
@login_required
@admin_required
def new_category():
    """Create a new category."""
    form = NewCategoryForm()
    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
        )
        db_session_add(category)
        
        flash('Category {} successfully created'.format(category.name),
              'form-success')
        new_form = NewCategoryForm()
        return render_template('admin/new_category.html', form=new_form)
    return render_template('admin/new_category.html', form=form)


@admin.route('/category/<int:category_id>')
@admin.route('/category/<int:category_id>/info')
@login_required
@admin_required
def category_info(category_id):
    """View a category's metadata."""
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        abort(404)
    return render_template('admin/manage_category.html', category=category)


@admin.route(
    '/category/<int:category_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def change_category(category_id):
    """Edit category."""
    category = Category.query.get(category_id)
    if category is None:
        abort(404)
    form = EditCategoryForm(obj=category)
    if form.validate_on_submit():
        form.populate_obj(category)
        db_session_add(category)
        
        flash('Category {} successfully updated.', 'form-success')
    return render_template('admin/manage_category.html', category=category, form=form)


@admin.route('/category/<int:category_id>/delete')
@login_required
@admin_required
def delete_category_request(category_id):
    """Request deletion of a category."""
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        abort(404)
    return render_template('admin/manage_category.html', category=category)


@admin.route('/category/<int:category_id>/_delete')
@login_required
@admin_required
def delete_category(category_id):
    """Delete a category."""
    category = Category.query.filter_by(id=category_id).first()
    db_session_delete(category)
        
    flash('Successfully deleted category', 'success')
    return redirect(url_for('admin.manage_categories'))


########################## Collection Management ##########################

@admin.route('/collection/<int:collection_id>')
@admin.route('/collection/<int:collection_id>/info')
@login_required
@admin_required
def collection_info(collection_id):
    """View a collection's metadata."""
    collection = Collection.query.filter_by(id=collection_id).first()
    if collection is None:
        abort(404)
    return render_template('admin/manage_collection.html', collection=collection)


@admin.route(
    '/collection/<int:collection_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def change_collection(collection_id):
    """Edit collection."""
    collection = Collection.query.get(collection_id)
    if collection is None:
        abort(404)
    form = EditCollectionForm(obj=collection)
    if form.validate_on_submit():
        form.populate_obj(collection)
        db_session_add(collection)
        
        flash('Collection {} successfully updated.', 'form-success')
    return render_template('admin/manage_collection.html', collection=collection, form=form)


@admin.route('/collection/<int:collection_id>/delete')
@login_required
@admin_required
def delete_collection_request(collection_id):
    """Request deletion of a collection."""
    collection = Collection.query.filter_by(id=collection_id).first()
    if collection is None:
        abort(404)
    return render_template('admin/manage_collection.html', collection=collection)


@admin.route('/collection/<int:collection_id>/_delete')
@login_required
@admin_required
def delete_collection(collection_id):
    """Delete a collection."""
    collection = Collection.query.filter_by(id=collection_id).first()
    db_session_delete(collection)
        
    flash('Successfully deleted collection', 'success')
    return redirect(url_for('admin.manage_collections'))


########################## Review new stories ##########################

@admin.route('/review')
@login_required
@admin_required
def review_stories():
    """Review new stories."""
    false_value = LookupValue.query.filter_by(group="bool",value="False").first()
    stories = Story.query.filter_by(origin="remote").filter_by(curated=false_value).all()
    return render_template('admin/review_stories.html', stories=stories)


@admin.route('/review/<int:story_id>')
@admin.route('/review/<int:story_id>/info')
@login_required
@admin_required
def review_story(story_id):
    """Review new story."""
    story = Story.query.filter_by(id=story_id).first()
    if story is None:
        abort(404)
    form = EditStoryForm(obj=story)
    if form.validate_on_submit():
        form.populate_obj(story)
        true_value = LookupValue.query.filter_by(group="bool",value="True").first()
        story.curated = true_value
        db_session_add(story)
        false_value = LookupValue.query.filter_by(group="bool",value="False").first()
        next_story = Story.query.filter_by(origin="remote").filter_by(curated=false_value).first()
        if next_story:
            next_form = EditStoryForm(obj=next_story)
            return render_template('admin/review_story.html', story=next_story, form=next_form)
        else:        
            return redirect(url_for('admin.review_stories'))
    return render_template('admin/review_story.html', story=story, form=form)