from flask import Blueprint, render_template, jsonify, request, redirect, url_for

from app.models import EditableHTML, Story, LookupValue
from app.main.forms import SearchForm
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


@main.route('/search/<terms>')
def search_list(terms):
    hits = []
    true_value = LookupValue.query.filter_by(group="bool",value="True").first()
    for term in terms.split():
        keyword = "%{}%".format(term)
        keyword = keyword.lower()
        stories_query = Story.query.filter(Story.feature_set.like(keyword)).all()
        for story in stories_query:
            if story not in hits:
                hits.append(story)
    return render_template('main/list.html', stories=hits, terms=terms, hits=len(hits))


@main.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        return jsonify(status='ok', url=url_for('main.search_list', terms=form.terms.data))
    return render_template('main/search.html', form=form, title="Search Stories")


@main.route('/view')
def view():
    id = request.args['id']
    story = Story.query.filter_by(id=id).first()
    if story is None:
        return jsonify('Bad id')
    return render_template(
        'main/view.html', oembed=story.oembed_full, title="Story")
    return