from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required

from app.models import EditableHTML, Story, LookupValue
from sqlalchemy import func

main = Blueprint('main', __name__)


@main.route('/')
def index():
    true_value = LookupValue.query.filter_by(group="bool",value="True").first()
    stories_query = Story.query.filter_by(visible=true_value).order_by(func.random())
    stories = stories_query.all()
    return render_template('main/index.html', stories=stories[:18], num=len(stories))


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template(
        'main/about.html', editable_html_obj=editable_html_obj)

@main.route('/search')
def search():
    # TODO get modal and post results/key
    return


@main.route('/view')
def view():
    id = request.args['id']
    story = Story.query.filter_by(id=id).first()
    if story is None:
        return jsonify('Bad id')
    return render_template(
        'main/view.html', oembed=story.oembed_full, title="Story")
    return