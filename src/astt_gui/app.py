import logging
import time
import os
from datetime import datetime
from threading import Lock

from flask import Flask, jsonify, render_template, request
from flask_socketio import SocketIO

from component_managers.astt_comp_manager import ASTTComponentManager
from component_managers.start_simulator import SimulatorManager

thread = None
thread_lock = Lock()
thread2 = None
thread3 = None

app = Flask(__name__)
app.config["SECRET_KEY"] = "STT"
socketio = SocketIO(app, cors_allowed_origins="*")

cm = ASTTComponentManager()
logger = logging.getLogger("ASTT-GUI")

logging.basicConfig(
    filename="app_dev.log",
    format="%(asctime)s|%(levelname)s|%(name)s|%(message)s",
    level=logging.INFO,
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_current_datetime():
    now = datetime.now()
    return now.strftime("%m/%d/%Y %H:%M:%S")


def background_thread(node):
    """Feeds az & el to the GUI."""
    if node is not None:
        while True:
            node.tpdo[1].wait_for_reception()
            node.tpdo[2].wait_for_reception()
            az = node.tpdo[
                "Position Feedback.Azimuth(R64) of position"
            ].raw
            el = node.tpdo[
                "Position Feedback.Elevation(R64) of position"
            ].raw
            socketio.emit(
                "updateAZELData",
                {"az": az, "el": el, "date": get_current_datetime()},
            )
            socketio.sleep(1)


def states_and_modes_thread(comp_manager):
    logger.info("Thread triggered")
    while True:
        func_state = comp_manager.antenna_func_state.name
        mode = comp_manager.antenna_mode.name
        stow_pin_state = comp_manager.stow_sensor_state.name
        if func_state and mode is not None:
            socketio.emit(
                "updateStateMode",
                {
                    "mode": str(mode),
                    "funcState": str(func_state),
                    "stowPinState": str(stow_pin_state),
                },
            )
            socketio.sleep(1)
        logger.info("SENT")


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")



@app.route("/", methods=["POST"])
def start_astt_gui():
    global thread, thread2, thread3  # Declare all global variables at once

    # Check the content type of the request
    if request.content_type == 'application/json':
        data = request.get_json()
        if "button" in data and data["button"] == "Initialize":
            user_pass = data.get("password")
            cm.clear_all_logs()
            logger.info("Initialized button triggered")
            simulator_manager = SimulatorManager()
            logger.info("Starting vcan interface")
            logger.info("Passing user password")
            print(f"Received password: {user_pass}")
            app.logger.debug(f"Received password: {user_pass}")
            success = simulator_manager.start_can_interface(user_pass)
            
            if success == 0:
                logger.info("Correct password")
                simulator_manager.run_container_and_startup_simulator()
                time.sleep(2)
                cm.connect_to_network()
                cm.connect_to_plc_node()
                cm.subscribe_to_az_change()
                cm.subscribe_to_el_change()
                cm.subscribe_to_func_state()
                cm.subscribe_to_mode_command_obj()
                cm.subscribe_to_antenna_mode()
                cm.subscribe_to_stow_sensor()
                cm.trigger_transmission()
                with thread_lock:
                    if thread3 is None:
                        thread3 = socketio.start_background_task(
                            states_and_modes_thread, cm
                        )
                return jsonify("success")
            else:
                logger.warn("Incorrect password entered")
                return jsonify("Wrong password, try again!!")
        elif "azimuth" in data and "elevation" in data:
            logger.info("Pointing button triggered")
            az = data["azimuth"]
            el = data["elevation"]
            try:
                cm.point_to_coordinates(
                    float(time.time()), float(az), float(el)
                )
            except (Exception, ValueError) as err:
                logger.error(f"Error encountered: {err}")
            with thread_lock:
                if thread is None:
                    thread = socketio.start_background_task(
                        background_thread, cm.antenna_node
                    )
        elif "sources" in data and data["sources"] == "sun":
            logger.info("Tracking button triggered")
            with thread_lock:
                if thread2 is None:
                    thread2 = socketio.start_background_task(
                        background_thread, cm.antenna_node
                    )
            cm.track_sun(1)
        elif "modes" in data:
            mode = data["modes"]
            if mode == "Idle":
                cm.set_idle_mode()
            elif mode == "Stow":
                cm.set_stow_mode()
            elif mode == "Point":
                cm.set_point_mode()
        return jsonify("Handled JSON request")
    
    elif request.content_type == 'application/x-www-form-urlencoded':
        if "button" in request.form and request.form["button"] == "Initialize":
            user_pass = request.form.get("password")
            cm.clear_all_logs()
            logger.info("Initialized button triggered")
            simulator_manager = SimulatorManager()
            logger.info("Starting vcan interface")
            logger.info("Passing user password")
            print(f"Received password: {user_pass}")
            app.logger.debug(f"Received password: {user_pass}")
            success = simulator_manager.start_can_interface(user_pass)
            
            if success == 0:
                logger.info("Correct password")
                simulator_manager.run_container_and_startup_simulator()
                time.sleep(2)
                cm.connect_to_network()
                cm.connect_to_plc_node()
                cm.subscribe_to_az_change()
                cm.subscribe_to_el_change()
                cm.subscribe_to_func_state()
                cm.subscribe_to_mode_command_obj()
                cm.subscribe_to_antenna_mode()
                cm.subscribe_to_stow_sensor()
                cm.trigger_transmission()
                with thread_lock:
                    if thread3 is None:
                        thread3 = socketio.start_background_task(
                            states_and_modes_thread, cm
                        )
                return jsonify("success")
            else:
                logger.warn("Incorrect password entered")
                return jsonify("Wrong password, try again!!")
        elif "azimuth" in request.form and "elevation" in request.form:
            logger.info("Pointing button triggered")
            az = request.form["azimuth"]
            el = request.form["elevation"]
            try:
                cm.point_to_coordinates(
                    float(time.time()), float(az), float(el)
                )
            except (Exception, ValueError) as err:
                logger.error(f"Error encountered: {err}")
            with thread_lock:
                if thread is None:
                    thread = socketio.start_background_task(
                        background_thread, cm.antenna_node
                    )
        elif "sources" in request.form and request.form["sources"] == "sun":
            logger.info("Tracking button triggered")
            with thread_lock:
                if thread2 is None:
                    thread2 = socketio.start_background_task(
                        background_thread, cm.antenna_node
                    )
            cm.track_sun(1)
        elif "modes" in request.form:
            mode = request.form["modes"]
            if mode == "Idle":
                cm.set_idle_mode()
            elif mode == "Stow":
                cm.set_stow_mode()
            elif mode == "Point":
                cm.set_point_mode()
        return render_template("index.html")
    
    else:
        return "Unsupported Media Type", 415


def connect():
    global thread

    print("Client connected")

    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(
                background_thread, cm.antenna_node
            )


"""
Decorator for disconnect.
"""


def disconnect():
    print("Client disconnected", request.sid)


if __name__ == "__main__":
    print("App started")
    socketio.run(app, host="0.0.0.0", port=5000)
