import datetime
from functools import wraps
from flask import Flask, render_template, redirect, url_for, request, send_from_directory, session, flash
from flask_bootstrap import Bootstrap5
from flask_ckeditor import CKEditor, CKEditorField
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Text, ARRAY
import os
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.choices import SelectField
from wtforms.fields.simple import EmailField, URLField
from wtforms.validators import DataRequired, URL
from socket import gethostname
from dotenv import load_dotenv
import smtplib

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_KEY')
ckeditor = CKEditor(app)
Bootstrap5(app)


# CREATE DATABASE
class Base(DeclarativeBase):
	pass


app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///projects.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Configure Project Table
class Project(db.Model):
	__tablename__ = "projects"
	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
	subtitle: Mapped[str] = mapped_column(String(50), nullable=True)
	category: Mapped[str] = mapped_column(String(30), nullable=False)
	date_finished: Mapped[str] = mapped_column(String(250), nullable=False)
	description: Mapped[str] = mapped_column(Text, nullable=False)
	goal: Mapped[str] = mapped_column(String(250), nullable=True)
	methods: Mapped[str] = mapped_column(String(250), nullable=True)
	challenges: Mapped[str] = mapped_column(String(250), nullable=True)
	tools: Mapped[str] = mapped_column(String(250), nullable=True)
	sources: Mapped[str] = mapped_column(String(250), nullable=True)
	improvements: Mapped[str] = mapped_column(String(250), nullable=True)
	tags: Mapped[str] = mapped_column(Text, nullable=True)
	img_url: Mapped[str] = mapped_column(String(250), nullable=False)
	img_alt_text: Mapped[str] = mapped_column(String(250), nullable=True)
	github_url: Mapped[str] = mapped_column(String(250), nullable=False)


# WTForm for creating a blog post
class CreateProjectForm(FlaskForm):
	title = StringField("Project Title", validators=[DataRequired()])
	subtitle = StringField("Project Subtitle")
	category = SelectField("Type of Project",
						   choices=["Data Analysis", "Web Design & Development", "Game Design", "Other"],
						   validators=[DataRequired()]
						   )
	date_finished = StringField("Date Completed (mm-yyyy)")
	description = CKEditorField("Project Description", validators=[DataRequired()])
	goal = CKEditorField("Project Goal / Why This Project")
	methods = CKEditorField("Project Methods")
	challenges = CKEditorField("Project's Greatest Challenge")
	tools = CKEditorField("Tools Used to Complete the Project")
	sources = CKEditorField("Project Data Sources")
	improvements = CKEditorField("Future Improvements")
	tags = StringField("Project Tags (separate with ',')")
	img_url = StringField("Blog Image URL", validators=[DataRequired(), URL()])
	img_alt_text = StringField("Alt Text for Image", validators=[DataRequired()])
	github_url = URLField("Github URL")
	submit = SubmitField("Submit Project")


# WTForm for contact page
class CreateContactForm(FlaskForm):
	name = StringField("Name", validators=[DataRequired()])
	email = EmailField("Email Address", validators=[DataRequired()])
	phone = StringField("Phone Number", validators=[DataRequired()])
	message = CKEditorField("Message", validators=[DataRequired()])
	submit = SubmitField("Submit Message")


with app.app_context():
	db.create_all()

site_password = os.getenv('SECRET_URL')


# custom decorator to check password
def check_pw(func):
	@wraps(func)
	def decorated_function(*args, **kwargs):
		status = session.get('status')
		if status != "good":
			return redirect(url_for('login'))
		return func(*args, **kwargs)

	return decorated_function


@app.route('/', methods=["GET", "POST"])
def home():
	#contact section
	form = CreateContactForm()
	if form.validate_on_submit():
		send_email(form.name.data, form.email.data, form.phone.data, form.message.data)
		return redirect(url_for("home"))
	#project section
	result = db.session.execute(db.select(Project))
	all_projects = result.scalars().all()
	return render_template("index_allpages.html", form=form, all_projects=all_projects)

@app.route('/download')
def download():
	return send_from_directory('static', path="files/LydiaKidwell_Resume_2025.pdf")

# @app.route(f"/{os.getenv('SECRET_URL')}", methods=["GET", "POST"])
@app.route("/add-project", methods=["GET", "POST"])
@check_pw
def add_project():
	form = CreateProjectForm()
	if form.validate_on_submit():
		new_project = Project(
				title=form.title.data,
				subtitle=form.subtitle.data,
				category=form.category.data,
				date_finished=form.date_finished.data,
				description=form.description.data,
				goal=form.goal.data,
				methods=form.methods.data,
				challenges=form.challenges.data,
				tools=form.tools.data,
				sources=form.sources.data,
				improvements=form.improvements.data,
				tags=form.tags.data,
				img_url=form.img_url.data,
				img_alt_text=form.img_alt_text.data,
				github_url=form.github_url.data
				)
		db.session.add(new_project)
		db.session.commit()
		return redirect(url_for("show_project", project_id=new_project.id))
	return render_template("add_project.html", form=form)


@app.route("/edit-project-<int:project_id>", methods=["GET", "POST"])
@check_pw
def edit_project(project_id):
	project = db.get_or_404(Project, project_id)
	edit_form = CreateProjectForm(
			title=project.title,
			subtitle=project.subtitle,
			category=project.category,
			date_finished=project.date_finished,
			description=project.description,
			goal=project.goal,
			methods=project.methods,
			challenges=project.challenges,
			tools=project.tools,
			sources=project.sources,
			improvements=project.improvements,
			tags=project.tags,
			img_url=project.img_url,
			img_alt_text=project.img_alt_text,
			github_url=project.github_url
			)
	if edit_form.validate_on_submit():
		project.title = edit_form.title.data
		project.subtitle = edit_form.subtitle.data
		project.category = edit_form.category.data
		project.date_finished = edit_form.date_finished.data
		project.description = edit_form.description.data
		project.goal = edit_form.goal.data
		project.methods = edit_form.methods.data
		project.challenges = edit_form.challenges.data
		project.tools = edit_form.tools.data
		project.sources = edit_form.sources.data
		project.improvements = edit_form.improvements.data
		project.tags = edit_form.tags.data
		project.img_url = edit_form.img_url.data
		project.img_alt_text = edit_form.img_alt_text.data
		project.github_url = edit_form.github_url.data

		db.session.commit()

		return redirect(url_for("show_project", project_id=project.id))

	return render_template("add_project.html", form=edit_form, is_edit=True)


@app.route("/project-<int:project_id>", methods=["GET", "POST"])
def show_project(project_id):
	description_components = ["Goal", "Methods", "Challenges", "Tools", "Sources", "Improvements", "Github"]
	requested_project = db.get_or_404(entity=Project, ident=project_id)

	return render_template("project.html", project=requested_project,
						   description_components=description_components)
@app.route("/steve")
def steve():
	# Show directory contents
	dir = "static/images/steve"
	return render_template('steve.html', files=get_imgs_path(dir))

@app.route("/certificates")
def certificates():
	# Show directory contents
	dir = "static/images/certificates"
	return render_template('steve.html', files=get_imgs_path(dir))

MAIL_ADDRESS = os.getenv("MY_EMAIL")
MAIL_APP_PW = os.getenv("EMAIL_APP_PASS")


@app.route("/contact", methods=["GET", "POST"])
def contact():
	form = CreateContactForm()
	if form.validate_on_submit():
		send_email(form.name.data, form.email.data, form.phone.data, form.message.data)
		return redirect(url_for("contact", msg_sent=True))
	return render_template("contact_form.html", form=form, msg_sent=False)


def send_email(name, email, phone, message):
	email_message = f"Subject:New Message\n\nName: {name}\nEmail: {email}\nPhone: {phone}\nMessage:{message}"
	with smtplib.SMTP("smtp.gmail.com") as connection:
		connection.starttls()
		connection.login(user=MAIL_ADDRESS, password=MAIL_APP_PW)
		connection.sendmail(from_addr=email, to_addrs=MAIL_ADDRESS, msg=email_message)


@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method == "POST":
		if request.form.get("password") != site_password:
			flash('wrong password! try again...')
			return redirect(request.url)
		else:
			session["status"] = 'good'
			return redirect(url_for("home"))
	return render_template('login.html')


@app.context_processor
def add_year():
	return {"current_year": str(datetime.datetime.now().year)}

def get_imgs_path(directory):
	files = os.listdir(directory)
	files_list = [directory + "/" + file for file in files]
	return files_list


if __name__ == "__main__":
	print(os.getenv('SECRET_URL'))
	app.run(debug=True, port=5001)
