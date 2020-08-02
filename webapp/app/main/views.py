from flask import Blueprint, render_template, jsonify, request, redirect, url_for
from flask import json

from app.models import EditableHTML, Story, LookupValue, Category
from app.main.forms import SearchForm
from sqlalchemy import func
from random import shuffle

main = Blueprint('main', __name__)

BASE="https://test.nottheonlyone.org"

@main.route('/')
def index():
    front_page = Category.query.filter_by(name="Front Page").first()
    if front_page is None:
        true_value = LookupValue.query.filter_by(group="bool",value="True").first()
        stories_query = Story.query.filter_by(visible=true_value).order_by(func.random())
        stories = stories_query.all()
        stories = stories[:18]
    else:
        stories = front_page.stories
        shuffle(stories)
    categories = []
    story_categories = Category.query.all()
    num = len(Story.query.all())
    for cat in story_categories:
        if cat.name != "Front Page":
            category = {}
            category['url'] = url_for("main.category", category_id=cat.id)
            category['name'] = '#' + cat.name.replace(' ', '')
            categories.append(category)
    return render_template('main/index.html', stories=stories, num=num, categories=categories)


@main.route('/about')
def about():
    editable_html_obj = EditableHTML.get_editable_html('about')
    return render_template('main/about.html', editable_html_obj=editable_html_obj)


@main.route('/search/<terms>')
def search_list(terms):
    hits = []
    true_value = LookupValue.query.filter_by(group="bool",value="True").first()
    share_url = BASE + url_for("main.search_list", terms=terms)
    for term in terms.split():
        keyword = "%{}%".format(term)
        keyword = keyword.lower()
        stories_query = Story.query.filter(Story.feature_set.like(keyword)).filter_by(visible=true_value).all()
        for story in stories_query:
            if story not in hits:
                hits.append(story)
    return render_template('main/list.html', stories=hits, title="Search Stories", terms=terms, hits=len(hits), share_url=share_url)


@main.route('/search', methods=['GET', 'POST'])
def search():
    form = SearchForm()
    if form.validate_on_submit():
        return jsonify(status='ok', url=url_for('main.search_list', terms=form.terms.data))
    return render_template('main/search.html', title="Search Stories", form=form)


@main.route('/view')
def view():
    id = request.args['id']
    story = Story.query.filter_by(id=id).first()
    share_url = BASE + url_for('main.story', story_id=story.id)
    if story is None:
        return jsonify('Bad id')
    categories = []
    if story.categories is not None:
        if len(story.categories) > 0:
            for cat in story.categories:
                if cat.name != "Front Page":
                    category = {}
                    category['url'] = url_for("main.category", category_id=cat.id)
                    category['name'] = '#' + cat.name.replace(' ', '')
                    categories.append(category)
    return render_template('main/view.html', oembed=story.oembed_full, share_url=share_url, categories=categories)


@main.route('/<story_id>')
def story(story_id):
    true_value = LookupValue.query.filter_by(group="bool",value="True").first()
    story = Story.query.filter_by(id=story_id).filter_by(visible=true_value).first()
    front_page = Category.query.filter_by(name="Front Page").first()
    if front_page is None:
        stories_query = Story.query.filter_by(visible=true_value).order_by(func.random())
        stories = stories_query.all()
        stories = stories[:18]
    else:
        stories = front_page.stories
        shuffle(stories)
    categories = []
    story_categories = Category.query.all()
    num = len(Story.query.all())
    for cat in story_categories:
        if cat.name != "Front Page":
            category = {}
            category['url'] = url_for("main.category", category_id=cat.id)
            category['name'] = '#' + cat.name.replace(' ', '')
            categories.append(category)
    if story is None:
        return render_template('main/index.html', stories=stories, num=len(stories), categories=categories)
    return render_template('main/index.html', stories=stories, num=num, load_id=story.id, categories=categories)


@main.route('/category/<category_id>')
def category(category_id):
    true_value = LookupValue.query.filter_by(group="bool",value="True").first()
    category = Category.query.filter_by(id=category_id).first()
    if category is None:
        return jsonify("Bad ID")
    
    share_url = BASE + url_for("main.category", category_id=category_id)
    stories = []
    for story in category.stories:
        if story.visible == true_value:
            stories.append(story)
    return render_template('main/list.html', share_url=share_url, title=category.name, stories=stories, hits=len(stories))