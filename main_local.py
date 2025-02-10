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
class Projects(db.Model):
	__tablename__ = "projects"
	id: Mapped[int] = mapped_column(Integer, primary_key=True)
	title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
	subtitle: Mapped[str] = mapped_column(String(50), nullable=True)
	category: Mapped[str] = mapped_column(String(30), nullable=False)
	date_finished: Mapped[str] = mapped_column(String(250), nullable=False)
	description: Mapped[str] = mapped_column(Text, nullable=False)
	tags: Mapped[str] = mapped_column(Text, nullable=True)
	img_url: Mapped[str] = mapped_column(String(250), nullable=False)
	img_alt_text: Mapped[str] = mapped_column(String(250), nullable=True)
	github_url: Mapped[str] = mapped_column(String(250), nullable=False)


with app.app_context():
	db.create_all()


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
	tags = StringField("Project Tags (separate with ','")
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


@app.route('/')
def home():
	return render_template("index.html", status="home")


@app.route("/about")
def about():
	# for pythonanywhere
	# with open("/home/lydiak22/mysite/PortfolioWebsite/about.txt", mode="r") as about_file:
	with open("about.txt", mode="r") as about_file:
		# create a list of paragraphs for the about section
		about_text = about_file.read().split("CHUNK")
	return render_template("about.html", status="about", about_text=about_text)


@app.route("/resume", methods=["GET", "POST"])
def resume():
	return render_template("resume_style.html", status="resume")


@app.route('/download')
def download():
	return send_from_directory('static', path="files/LydiaKidwell_Resume_2025.pdf")


@app.route('/projects')
def projects():
	result = db.session.execute(db.select(Projects))
	all_projects = result.scalars().all()
	return render_template("all_projects_copy.html", all_projects=all_projects, status="projects")


# @app.route(f"/{os.getenv('SECRET_URL')}", methods=["GET", "POST"])
@app.route("/add-project", methods=["GET", "POST"])
@check_pw
def add_project():
	form = CreateProjectForm()
	if form.validate_on_submit():
		new_project = Projects(
				title=form.title.data,
				subtitle=form.subtitle.data,
				category=form.category.data,
				date_finished=form.date_finished.data,
				description=form.description.data,
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
	project = db.get_or_404(Projects, project_id)
	edit_form = CreateProjectForm(
			title=project.title,
			subtitle=project.subtitle,
			category=project.category,
			date_finished=project.date_finished,
			description=project.description,
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
		project.tags = edit_form.tags.data
		project.img_url = edit_form.img_url.data
		project.img_alt_text = edit_form.img_alt_text.data
		project.github_url = edit_form.github_url.data

		db.session.commit()

		return redirect(url_for("show_project", project_id=project.id, status="projects"))

	return render_template("add_project.html", form=edit_form, is_edit=True, status="projects")


# Add a POST method to be able to post comments
@app.route("/project-<int:project_id>", methods=["GET", "POST"])
def show_project(project_id):
	requested_project = db.get_or_404(entity=Projects, ident=project_id, description="This project does not exist.")

	return render_template("project.html", project=requested_project, status="projects")


MAIL_ADDRESS = os.getenv("MY_EMAIL")
MAIL_APP_PW = os.getenv("EMAIL_APP_PASS")


@app.route("/contact", methods=["GET", "POST"])
def contact():
	form = CreateContactForm()
	if form.validate_on_submit():
		send_email(form.name.data, form.email.data, form.phone.data, form.message.data)
		return redirect(url_for("contact", msg_sent=True, status="contact"))
	return render_template("contact_form.html", form=form, msg_sent=False, status="contact")


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
			return redirect(url_for("projects"))
	return render_template('login.html')


@app.context_processor
def add_year():
	return {"current_year": str(datetime.datetime.now().year)}


if __name__ == "__main__":
	print(os.getenv('SECRET_URL'))
	app.run(debug=True, port=5001)
