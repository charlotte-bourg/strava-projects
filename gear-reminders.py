from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run('0.0.0.0', debug=True)
    app.app_context().push()