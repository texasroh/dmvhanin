from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for, current_app,
)
from .filestream import upload_file_to_local, upload_file_to_s3
from . import db

bp = Blueprint('buynsell', __name__, url_prefix='/buynsell')

@bp.route('/', methods=('GET',))
def index():
    return render_template('buynsell/index.html')