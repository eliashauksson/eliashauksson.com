import os
from flask import Blueprint, current_app, redirect, render_template, request
from .markdown_utils import render_markdown
from .mail_utils import send_contact_message

bp = Blueprint("routes", __name__)


@bp.route("/")
def main():
    return redirect("/home")


@bp.route("/home")
def home():
    return render_template("home.html")


@bp.route("/about")
def about():
    # Load role texts from markdown files so longer content is easy to edit.
    content_dir = os.path.join(current_app.static_folder, "content")

    def load(name: str) -> str:
        path = os.path.join(content_dir, name)
        try:
            with open(path, "r", encoding="utf-8") as f:
                return render_markdown(f.read())
        except FileNotFoundError:
            return ""

    about_engineer = load("about_engineer.md")
    about_athlete = load("about_athlete.md")
    about_soldier = load("about_soldier.md")

    return render_template(
        "about.html",
        about_engineer=about_engineer,
        about_athlete=about_athlete,
        about_soldier=about_soldier,
    )


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    status = None
    error = None
    form = {"name": "", "email": "", "message": ""}

    if request.method == "POST":
        form["name"] = (request.form.get("name") or "").strip()
        form["email"] = (request.form.get("email") or "").strip()
        form["message"] = (request.form.get("message") or "").strip()
        honeypot = (request.form.get("company") or "").strip()  # hidden field bots may fill

        # basic validation
        if honeypot:
            error = "Submission flagged as spam."
        elif not form["name"] or not form["email"] or not form["message"]:
            error = "Please fill out your name, email, and message."
        elif "@" not in form["email"] or "." not in form["email"].split("@")[-1]:
            error = "Please provide a valid email address."
        else:
            ok, err = send_contact_message(form["name"], form["email"], form["message"])
            if ok:
                status = "Your message has been sent. Thank you!"
                form = {"name": "", "email": "", "message": ""}
            else:
                error = err or "Something went wrong while sending your message."

    return render_template("contact.html", status=status, error=error, form=form)


@bp.route("/projects")
def projects():
    return render_template("projects.html")
