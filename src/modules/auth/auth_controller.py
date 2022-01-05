from flask import Blueprint, jsonify, request, render_template, flash, current_app, url_for, make_response
from flask_login import login_required, current_user, logout_user, login_user
from werkzeug.utils import redirect

from src.main import limiter
from src.base.constants.base_constanst import FlashCategory
from src.modules.auth.auth_service import AuthService

# defining controller
auth = Blueprint('auth', __name__, template_folder='templates', static_folder='static', static_url_path='auth/static')


@auth.route('/login', methods=['GET', 'POST'])
def login():
    # grabbing the form
    from src.modules.auth.forms.login_form import LoginForm
    form = LoginForm()

    # checking if is GET request
    if request.method == 'GET':
        # redirecting logged-in user to the index page
        if current_user.is_authenticated:
            flash('You\'re already logged in!', category='warning')
            return redirect('/')

        if request.args.get('email'):
            form.email.data = request.args.get('email')
        return render_template('login.html', form=form)

    # POST REQUEST
    # checking if the form is not valid yet
    if not form.validate_on_submit():
        return render_template('login.html', form=form)

    # FORM IS VALID, LET'S GET THE USER OBJECT FROM DB
    from src.modules.user.user_model import User
    from src.main import db
    user = AuthService.get_user_from_email(form.email.data)
    
    if user is not None:
        # let's log the user in
        login_user(user, remember=form.remember)
        next_url = request.args.get('next')
        return redirect(next_url if next_url else '/')
    
    flash(message='The user no longer exists', category=FlashCategory.Error)
    return render_template('login.html', form=form)


@auth.route('/logout', methods=['POST'])
@limiter.limit('5/minute')
@login_required
def logout():
    logout_user()
    return redirect(location="/")


@auth.route('/register', methods=['GET', 'POST'])
@limiter.limit('1/second')
def register():
    # grabbing the form
    from src.modules.auth.forms.signup_form import SignUpForm
    form = SignUpForm()

    # checking if is GET request
    if request.method == 'GET':
        # redirecting logged-in user to the index page
        if current_user.is_authenticated:
            flash('Please logout first, then signup!', category=FlashCategory.warning())
            return redirect('/')
        return render_template('signup.html', form=form)

    # checking if the form is not valid yet
    if not form.validate_on_submit():
        flash('Please ensure all fields have no errors!', category=FlashCategory.warning(7500))
        return render_template('signup.html', form=form)

    # all validation passed, let's continue handle the signup process
    # envoy_type:4 == công ty/tổ chức/trường học
    AuthService.register(form)

    # showing a flash message -> redirecting to the home page
    flash(message=f'Vui lòng kiểm tra tin nhắn được gửi tới email {form.email.data} để kích hoạt tài khoản!', category=FlashCategory.success(20000))

    # showing the login page and auto filling data
    return redirect(url_for('auth.login', email=form.email.data))


@auth.route('/reset-password', methods=['POST'])
def reset_password():
    from src.modules.auth.auth_service import AuthService

    AuthService.send_reset_password_email(request.email)
    return "password reset", 200


@auth.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    from src.modules.auth.forms.profile_form import UpdateForm
    form = UpdateForm()

    from src.modules.user.user_model import User
    current_user_object = User.query.get(current_user.get_id())  # type: User

    # assigning current user's email for every requests --- the email field is not editable (primary key)
    form.email.data = current_user_object.email
    print('avatar:', form.avatar)


    # checking if is GET request
    if request.method == 'GET':
        # re-assigning the full_name to latest value
        form.full_name.data = current_user_object.full_name
        return render_template('profile.html', form=form)

    # checking if the form is not valid yet
    if not form.validate_on_submit():
        # re-assigning the full_name to reduce confusing
        form.full_name.data = current_user_object.full_name

        flash('form error !', category='error')
        return render_template('profile.html', form=form)


    # all validations passed, let's update the user's new data
    # saving the new avatar_url to the DB if a avatar choosen
    from src.modules.auth.auth_service import AuthService
    avatar_path = None
    print('image data:', form.avatar.data)
    if form.avatar.data:
        avatar_path = AuthService.save_avatar_image(form.avatar.data)
        print('saved avatar path:', avatar_path)

    try:
        # the avatar field now is not a file (via: request.files)
        if request.form['avatar'] == 'null':
            avatar_path = 'null'
    except:
        print('')

    # updating the user's new data
    user = User(full_name=form.full_name.data, avatar_url=avatar_path)
    AuthService.update(current_user.get_id(), user)


    flash('Updated !', category=FlashCategory.Success)
    return redirect(location='profile')


@auth.route('/check-email', methods=['POST'])
def check_email_exists():
    email = request.form.get('email', None)

    if email:
        from src.modules.auth.auth_service import AuthService

        if AuthService.is_user_already_exists(email):
            return {'exists': True}, 200
        else:
            response = jsonify({'message': 'The email is not registered.'})
            response.status_code = 404
            return response

    else:
        print('the email field is not exists')
        return {'error': 'form data missing.'}, 400

