import multiprocessing
import requests
import os

with open('configs/clients.config', 'r') as file:
    clients = file.read().splitlines()


def main():
    def get_ip_addresses():
        import netifaces

        interfaces = netifaces.interfaces()
        ips = []
        for interface in interfaces:
            if netifaces.AF_INET in netifaces.ifaddresses(interface):
                ips.append(netifaces.ifaddresses(interface)[netifaces.AF_INET][0]['addr'])
        return ips

    ip_addresses = get_ip_addresses()
    print("Select the ip address where the chat will be launched!")
    for index, ip in enumerate(ip_addresses, start=1):
        print(f"{index}) {ip}")
    while True:
        user_choice = input("Choose an IP address by entering its corresponding number: ")
        if user_choice.isnumeric():
            index = int(user_choice)
            if 1 <= index <= len(ip_addresses):
                host = ip_addresses[index - 1]
                nick = input("nick:")
                port = input("port:")
                server(host, nick, port)
                break
            else:
                print("Invalid input. Please enter a valid number.")
        else:
            print("Invalid input. Please enter a valid number.")


def server(host, nick, port):
    from markupsafe import escape
    from flask import Flask, request, render_template, jsonify
    from flask_wtf.csrf import CSRFProtect, validate_csrf
    from werkzeug.exceptions import BadRequest
    from waitress import serve
    import binascii

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

                multiprocessing.Process(target=send_message, args=(name, message)).start()

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

    print(f"Server running on http://{host}:{port}")
    serve(app, host=host, port=port)


def send_message(name, message):
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