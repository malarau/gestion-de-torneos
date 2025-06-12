# Used template:
# https://www.creative-tim.com/product/argon-dashboard-flask

if __name__ == "__main__":
    from flaskapp import create_app
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=True) # CHANGE THIS FOR PRODUCTION