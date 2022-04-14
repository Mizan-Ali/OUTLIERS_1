import re
import pymongo
from logger import Logger
from .user import get_user
from .constants import views_constants
from flask_login import login_required, current_user
from .models import mongo, save_github, save_codechef, save_codeforces
from flask import Blueprint, flash, redirect, render_template, url_for, request

logger = Logger(mongo)
views = Blueprint("views", __name__)


@views.route("/home")
def home():
    return render_template("home.html", user=current_user)


@views.route("/")
@login_required
def profile():
    return render_template("profile.html", user=current_user)


@views.route("/public_profile/<username>")
def public_profile(username):
    if not username:
        flash("Please enter a username", category="error")
        return redirect(url_for("view.profile"))

    friend = get_user(username=username)
    if friend is None:
        flash("User does not exist.", category="error")
        return redirect((url_for("views.profile")))

    return render_template(
        "public_profile.html",
        user=current_user,
        friend=friend
    )

@views.route("/search", methods=["POST"])
def search():
    username = request.form.get("username")
    if not username:
        flash("Enter a username", category="error")
        return redirect(url_for("views.profile"))

    users_collection = mongo.db.users
    user_list = list(users_collection.find({"$or": [{"_id": username}, {"github_username": username}, {"codechef_username": username}, {"codeforces": username}, {"full_name": re.compile(username, re.IGNORECASE)}]}, {"_id": 1, "github_username": 1, "codechef_username": 1, "codeforces_username": 1, "score": 1}))

    return render_template("search.html", user_list=user_list, user=current_user)


@views.route("/leaderboard")
def leaderboard():
    global_leaderboard = get_global_leaderboard()
    friends_leaderboard = get_friend_leaderboard()

    return render_template(
        "leaderboard.html",
        user=current_user,
        global_leaderboard=global_leaderboard,
        friends_leaderboard=friends_leaderboard,
    )


@views.route("/refresh_github", methods=["POST"])
@login_required
def refresh_github():
    try:
        save_github(current_user.github_username)
        flash("Updated GitHub", category="success")
    except Exception as e:
        flash("Unable to add Github", category="error")

    current_user.update_rating()
    return redirect(url_for("views.profile"))


@views.route("/refresh_codeforces", methods=["POST"])
@login_required
def refresh_codeforces():
    try:
        save_codeforces(current_user.codeforces_username)
        flash("Updated Codeforces", category="success")
    except Exception as e:
        flash("Unable to add Codeforces", category="error")

    current_user.update_rating()
    return redirect(url_for("views.profile"))


@views.route("/refresh_codechef", methods=["POST"])
@login_required
def refresh_codechef():
    try:
        save_codechef(current_user.codechef_username)
        flash("Updated Codechef", category="success")
    except Exception as e:
        flash("Unable to add Codechef", category="error")

    current_user.update_rating()
    return redirect(url_for("views.profile"))


def get_global_leaderboard():
    leaderboard = []
    users_collection = mongo.db.users
    for user in users_collection.find().sort("score", pymongo.DESCENDING):
        leaderboard.append((user["_id"], user.get("score", 0)))
    return leaderboard


def get_friend_leaderboard():
    if not current_user.is_authenticated:
        return [("Sign-In to view your personal leaderboard", "")]

    leaderboard = [(current_user.username, current_user.score)]

    users_collection = mongo.db.users
    for friend_username in current_user.friends:
        friend = users_collection.find_one({"_id": friend_username})
        leaderboard.append((friend["_id"], friend.get("score", 0)))
    leaderboard.sort(key=lambda x: x[-1], reverse=True)
    return leaderboard
