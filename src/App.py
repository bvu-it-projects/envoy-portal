from flask import Flask
import os

class App(Flask):
    def __init__(self, 
        # instance_path,
    ):
        super(App, self).__init__(
            import_name=__name__,
            # instance_path=instance_path,
            # instance_relative_config=True,
        )

        # assigning the base "templates" & "static" folder
        self.template_folder = './base/templates/'
        self.static_folder = './base/static/'

        # loading environment variables
        self.load_environment_variables()

        # registering essential partials for the app
        self.register_base_components()
        self.register_global_functions()
        self.register_blueprints()
        # self.register_cors()
        self.register_error_handlers()
        self.register_login_manager()


    def register_base_components(self):
        """
        Registering base app's components via context_processor to get called each time a new request coming.
        """
        # registering view components
        from .base.components.header.header_component import header_component
        from .base.components.sidebar.sidebar_component import sidebar_component
        self.context_processor(header_component)
        self.context_processor(sidebar_component)


    def register_global_functions(self):
        """
        Registering jinja global functions (allow calling from any jinja templates)
        """
        from .base.helpers.jinja_env_functions import extract_avatar_url, get_svg_content, server_name
        self.jinja_env.globals.update(extract_avatar_url=extract_avatar_url)
        self.jinja_env.globals.update(get_svg_content=get_svg_content)
        self.jinja_env.globals.update(server_name=server_name)


    def register_blueprints(self):
        """
        Registering the app's blueprints.
        """
        # PORTAL subdomain
        from .modules.home.home_controller import home
        from .modules.auth.auth_controller import auth
        from .modules.admission.admission_controller import admission
        from .modules.user.user_controller import user
        from .modules.mock.mock_controller import mock
        self.register_blueprint(home, url_prefix="/")
        self.register_blueprint(auth, url_prefix="/")
        self.register_blueprint(admission, url_prefix="/admissions")
        self.register_blueprint(user, url_prefix="/users")
        self.register_blueprint(mock, url_prefix="/mocks")


    def register_cors(self):
        """Adding CORS origins (all) for client ajax calling."""
        from flask_cors import CORS
        cors = CORS(app=self, resources={r"/*": {"origins": "*"}})


    def register_error_handlers(self):
        """
        Registering custom error handlers that show custom view (html page) for the src.
        """
        from .base.helpers.error_handlers import ErrorHandler

        self.register_error_handler(403, ErrorHandler.forbidden)
        self.register_error_handler(404, ErrorHandler.not_found)
        self.register_error_handler(429, ErrorHandler.too_many_requests)
        self.register_error_handler(500, ErrorHandler.server_error)


    def register_login_manager(self):
        """Adding login manager for the application."""
        from flask_login import LoginManager

        login_manager = LoginManager()
        login_manager.login_view = "auth.login"
        login_manager.init_app(self)

        @login_manager.user_loader
        def load_user(id):
            # register user_loader
            from .modules.user.user_model import User, db
            return db.session.query(User).filter(User.alternative_id == id).first()


    def load_environment_variables(self):
        """
        Loading the configured environment variables.
        """
        from dotenv import load_dotenv
        load_dotenv()  # take environment variables from .env file.
        print('/n', os.environ)

        # USING DEFAULT CONFIG
        from .config import DefaultEnvironment
        self.config.from_object(DefaultEnvironment)

        # LOAD/OVERRIDE DEVELOPER SPECIFIED ENV
        environment_configuration = os.environ.get('CONFIG_FILE')
        assert environment_configuration is not None, "Please provide the CONFIG_FILE env"
        self.config.from_object(environment_configuration)

        print('\n', self.config, '\n\n')
