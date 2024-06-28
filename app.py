from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/webhook", methods=["POST", "GET"])
async def webhook():
    if request.method == "POST":
        
        data = request.get_json()
        
        if request.content_type != 'application/json':
            return jsonify({"error": "Content-Type must be application/json"}), 415

        if data is None:
            return jsonify({"error": "Invalid JSON"}), 400

        print("\n\nIncoming webhook message:", data)
        # Add your processing logic here
        # Process the data received in the POST request

    elif request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == "123456":
            print("Webhook verified successfully!")
            return challenge, 200
        else:
            return "Forbidden", 403

    return jsonify({"message": "Webhook endpoint"}), 200

@app.route("/", methods=["GET"])
async def index():
    return "<pre>Nothing to see here.\nCheckout README.md to start.</pre>"

if __name__ == "__main__":
    app.run(port=1000, debug=True)
