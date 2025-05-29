# Used template:
# https://www.creative-tim.com/product/argon-dashboard-flask

if __name__ == "__main__":
    from flaskapp import create_app
    app = create_app()
    app.run(host="localhost", port=5000)