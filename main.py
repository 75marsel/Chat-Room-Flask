from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
from string import ascii_uppercase
from datetime import datetime
import random

# ASSIGNMENT 
# CREATE A DATABASE OF CHATLOGS AND ACCOUNTS

ROOM_CODE_LENGTH: int = 4

app = Flask(__name__)
app.config["SECRET_KEY"] = "sample"
socketio = SocketIO(app)

rooms: dict = {}

def get_date_time_today() -> int:
    return datetime.now().strftime("%m-%d-%Y %I:%M:%S %p")

def generate_unique_code(length: int) -> int:
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
        
    return code

@app.route('/', methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        create = request.form.get("create", False)
        join = request.form.get("join", False)

        if not name:
            return render_template("home.html", error="Please enter a name!", code=code, name=name)
        
        if join != False and not code:
            return render_template("home.html", error="Please enter a room code!", code=code, name=name)

        room = code
        if create != False:
            room = generate_unique_code(ROOM_CODE_LENGTH) 
            rooms[room] = {"members": 0, "messages": [], "members_username": []}
        elif code not in rooms:
            return render_template("home.html", error="Room does not exist!", code=code, name=name)
        
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
        
    return render_template("home.html")


@app.route("/room")
def room():
    username = session.get("name")
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    
    print("current messages: ")
    print(rooms[room]["messages"])
    
    print("current members: ")
    print(rooms[room]["members"])
    
    print("current members: ")
    print(rooms[room]["members_username"])
    
    return render_template("room.html", code=room, username=username, messages=rooms[room]["messages"])

@socketio.on("message")
def message(data):
    room = session.get("room")
    if room not in rooms:
        return
    
    date_time_today = get_date_time_today()
    
    content = {
        "name": session.get("name"),
        "message": data["data"],
        "date": date_time_today
    }
    
    send(content, to=room)
    rooms[room]["messages"].append(content)
    print(f"{session.get('name')} said: {data['data']}")
    print("current members: ")
    print(rooms[room]["members"])

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    
    if not room or not name:
        return
    
    if room not in rooms:
        leave_room(room)
        return

    date_time_today = get_date_time_today()
    
    join_room(room)
    send({"name": name, "message": "has entered the room!", "date": date_time_today}, to=room)
    if(name not in rooms[room]["members_username"]):
        rooms[room]["members"] += 1
        rooms[room]["members_username"].append(name)
    
    print(f"{name} joined the room {room}")

@socketio.on("disconnect")
@socketio.on("disconnect_req")
def disconnect(data=None):
    room = session.get("room")
    name = session.get("name")
    date_time_today = get_date_time_today()

    if data is None and room in rooms:

        if rooms[room]["members"] < 1:
            
            print("in data is none and less than 1")
            leave_chat_room(name, room, date_time_today)
    
    if data is not None and data["username"] == name:
        print(f"check username: {data['username']} and name: {name}")
        leave_chat_room(name, room, date_time_today)
        socketio.emit("redirectUser", {"username": data['username'],"url": url_for("home")}) 
        print(f"{name} has left the room {room}")

def leave_chat_room(name, room, date_time_today):
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    
    date_time_today = get_date_time_today()
    
        
    date_time_today = get_date_time_today()
    
    send({"name": name, "message": "has left the room", "date": date_time_today}, to=room)


if __name__ == '__main__':
    socketio.run(app)