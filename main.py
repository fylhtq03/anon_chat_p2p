import multiprocessing


def main():
    loads_configs()
    process_server = multiprocessing.Process(target=server, args=(host, port, nick, clients))
    process_server.start()
    print(f'http://{host}:{port}')


def loads_configs():
    global clients, host, port, nick
    config = {}

    with open('configs/clients.config', 'r') as file:
        clients = file.read().splitlines()

    with open('configs/config.config', 'r') as file:
        for line in file:
            key, value = line.strip().split('=')
            config[key] = value

    host = config.get('ip', '')
    port = config.get('port', '')
    nick = config.get('nick', '')


def server(host, port, nick, clients):
    from markupsafe import escape
    from flask import Flask, request, render_template, jsonify
    from flask_wtf.csrf import CSRFProtect, validate_csrf
    from werkzeug.exceptions import BadRequest
    from waitress import serve
    import binascii
    import os

    messages = []

    app = Flask(__name__)
    app.secret_key = binascii.hexlify(os.urandom(2048)).decode()
    CSRFProtect(app)

    @app.route("/")
    def index():
        if request.remote_addr == host:
            return render_template("index.html", nick=nick)
        else:
            return ""

    @app.route('/post_message', methods=['POST'])
    def post_message():
        try:
            csrf_token = request.form.get('csrf_token')
            validate_csrf(csrf_token)

            if request.remote_addr == host:
                message = request.form['message']
                name = request.form['name']

                multiprocessing.Process(target=send_message, args=(name, message, clients)).start()

                if name == nick:
                    safe_name = escape(name)
                    safe_message = escape(message)
                    messages.append({'name': safe_name, 'message': safe_message})

                return jsonify({'status': 'OK'})
            else:
                return jsonify({'status': 'error', 'message': 'Unauthorized'}), 403

        except BadRequest:
            return jsonify({'status': 'error', 'message': 'CSRF token missing or incorrect'}), 403

    @app.route('/get_messages')
    def get_messages():
        if request.remote_addr == host:
            return jsonify(messages)
        else:
            return ""

    @app.route("/message")
    def get_message():
        message = request.args.get("message")
        name = request.args.get("name")
        safe_name = escape(name)
        safe_message = escape(message)
        print(safe_message)
        messages.append({'name': safe_name, 'message': safe_message})
        return "Ok"

    serve(app, host=host, port=port)


def send_message(name, message, clients):
    import requests
    if message == "" or name == "":
        pass
    else:
        for url in clients:
            print(f'message:"{message}" name:"{name}", sender:{url}')
            try:
                requests.get(f"http://{url}/message?message={message}&name={name}", timeout=5)
            except:
                print(f'Error sending message')
    exit()


if __name__ == '__main__':
    multiprocessing.freeze_support()
    main()