from ursina import *
from direct.actor.Actor import Actor
import cv2
import mediapipe as mp
import random
from PIL import Image

app = Ursina()

# --- KONFIGURACJA MEDIAPIPE ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    max_num_hands=1,
    min_detection_confidence=0.6,
    min_tracking_confidence=0.6
)

def classify_rps(hand_landmarks, handedness):
    lm = hand_landmarks.landmark
    # Prosta logika rozpoznawania na podstawie Twojego pliku v3
    index_up  = lm[8].y  < lm[6].y
    middle_up = lm[12].y < lm[10].y
    ring_up   = lm[16].y < lm[14].y
    pinky_up  = lm[20].y < lm[18].y
    
    thumb_tip = lm[4]
    thumb_ip = lm[3]
    if handedness == "Right":
        thumb_up = thumb_tip.x > thumb_ip.x
    else:
        thumb_up = thumb_tip.x < thumb_ip.x

    up_count = sum([thumb_up, index_up, middle_up, ring_up, pinky_up])

    if up_count <= 1 and not any([index_up, middle_up, ring_up, pinky_up]):
        return "rock"
    if up_count >= 4 and all([index_up, middle_up, ring_up, pinky_up]):
        return "paper"
    if index_up and middle_up and not ring_up and not pinky_up:
        return "scissors"
    return "unknown"

# --- ŚWIATŁO I MODEL 3D ---
Entity(model='directional_light', rotation=(45, 45, 0))
hand_actor = Actor("../assets/reka/hand2.glb")
hand_actor.reparentTo(scene)
hand_actor.setScale(5)
hand_actor.setPos(0, -10, 2)

bone_names = [
    "nadgarstek", "Przed_kciuk", "kciuk1", "kciuk2",
    "przed_wskazujacy", "wskazujacy1", "wskazujacy2", "wskazujacy3",
    "przed_srodkowy", "srodkowy1", "srodkowy2", "srodkowy3",
    "przed_serdeczny", "serdeczny1", "serdeczny2", "serdeczny3",
    "przed_maly", "maly1", "maly2", "maly3"
]

bones = {name: hand_actor.controlJoint(None, "modelRoot", name) for name in bone_names}
active_anims = []

# Słowniki pozycji z pliku ruchoma_reka_v3.py
RockPose = {
    "nadgarstek": (228.051, 2.718, -1.647),
    "Przed_kciuk": (-36.854, -10.847, -43.296),
    "kciuk1": (-33.872, -77.426, 16.048),
    "kciuk2": (-40.845, -0.647, -11.039),
    "przed_wskazujacy": (0.411, -1.781, -21.090),
    "wskazujacy1": (1.058, -93.412, 8.448),
    "wskazujacy2": (3.708, -66.794, 5.106),
    "wskazujacy3": (-0.429, -73.539, -1.233),
    "przed_srodkowy": (0.294, -0.951, -6.095),
    "srodkowy1": (1.814, -106.516, 3.905),
    "srodkowy2": (-0.810, -65.364, -1.206),
    "srodkowy3": (-8.365, -76.276, -0.465),
    "przed_serdeczny": (0.466, -0.135, 10.456),
    "serdeczny1": (-1.728, -106.678, -5.509),
    "serdeczny2": (-0.594, -94.493, -0.097),
    "serdeczny3": (-1.898, -76.531, -2.716),
    "przed_maly": (5.128, -4.124, 22.038),
    "maly1": (-1.541, -96.518, 1.544),
    "maly2": (-2.290, -94.469, -6.484),
    "maly3": (3.536, -82.711, -0.384),
}

PapierPose = {
    "nadgarstek": (0.062, 2.718, -1.647),
    "Przed_kciuk": (-11.522, -17.013, -49.796),
    "kciuk1": (4.126, -1.429, 16.048),
    "kciuk2": (-2.847, -0.647, -11.039),
    "przed_wskazujacy": (0.411, -1.781, -14.923),
    "wskazujacy1": (1.058, -17.416, 8.448),
    "wskazujacy2": (3.708, -9.797, 7.572),
    "wskazujacy3": (-0.429, 2.457, -1.233),
    "przed_srodkowy": (0.294, -0.951, -6.095),
    "srodkowy1": (1.814, -24.187, 3.905),
    "srodkowy2": (-0.810, -8.367, -1.206),
    "srodkowy3": (-8.365, -0.280, -0.465),
    "przed_serdeczny": (0.466, -0.135, 4.223),
    "serdeczny1": (-1.728, -30.682, -9.209),
    "serdeczny2": (-0.594, -5.831, -0.097),
    "serdeczny3": (-1.898, -0.535, -2.716),
    "przed_maly": (5.128, -4.124, 12.171),
    "maly1": (-1.541, -20.522, -8.322),
    "maly2": (-2.290, -5.806, -6.484),
    "maly3": (3.536, -6.714, -0.384),
}
ScissorsPose = {
    "nadgarstek": (0.062, 2.718, -1.647),
    "Przed_kciuk": (-35.542, -10.847, -43.953),
    "kciuk1": (-31.903, -73.488, 16.048),
    "kciuk2": (-38.876, -0.647, -11.039),
    "przed_wskazujacy": (6.416, -1.781, -21.090),
    "wskazujacy1": (1.058, -17.416, 8.448),
    "wskazujacy2": (3.708, -9.797, 5.106),
    "wskazujacy3": (-0.429, 2.457, -1.233),
    "przed_srodkowy": (-11.715, -0.951, -6.095),
    "srodkowy1": (1.814, -24.187, 3.905),
    "srodkowy2": (-0.810, -8.367, -1.206),
    "srodkowy3": (-8.365, -0.280, -0.465),
    "przed_serdeczny": (0.466, -0.135, 10.324),
    "serdeczny1": (-1.728, -102.740, -5.509),
    "serdeczny2": (-0.594, -89.899, -0.097),
    "serdeczny3": (-1.898, -72.593, -2.716),
    "przed_maly": (5.128, -4.124, 22.038),
    "maly1": (-1.541, -92.580, 1.544),
    "maly2": (-2.290, -89.874, -6.484),
    "maly3": (3.536, -78.773, -0.384),
}
Poses = {"rock": RockPose, "paper": PapierPose, "scissors": ScissorsPose}

def start_pose_anim(pose_name, duration=0.5):
    if pose_name not in Poses: return
    pose_data = Poses[pose_name]
    for b_name, target_hpr in pose_data.items():
        if b_name in bones:
            active_anims.append({
                "bone": bones[b_name],
                "start": bones[b_name].getHpr(),
                "target": target_hpr,
                "time": duration,
                "t": 0
            })

# --- UI I KAMERA ---
camera.position = (5, 4.5, -7.5)
camera.rotation = (48, -28, 0)
cap = cv2.VideoCapture(2)
camera_view = Entity(model='quad', parent=camera.ui, scale=(0.4, 0.3), position=(0.6, -0.3))
info_text = Text(text="SPACE - START", origin=(0,0), y=0.4, scale=2)

game_state = "IDLE"
countdown = 0

def update():
    global game_state, countdown
    
    ret, frame = cap.read()
    current_gesture = "unknown"
    if ret:
        frame = cv2.flip(frame, 1)
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        
        if results.multi_hand_landmarks:
            land = results.multi_hand_landmarks[0]
            hand_type = results.multi_handedness[0].classification[0].label
            current_gesture = classify_rps(land, hand_type)
        
        # FIX dla AttributeError: konwersja do PIL Image
        img_pil = Image.fromarray(cv2.resize(rgb, (400, 300)))
        camera_view.texture = Texture(img_pil)

    # Maszyna stanów
    if game_state == "COUNTDOWN":
        countdown -= time.dt
        info_text.text = str(int(countdown) + 1)
        if countdown <= 0:
            comp_move = random.choice(["rock", "paper", "scissors"])
            start_pose_anim(comp_move)
            info_text.text = f"Twoj ruch: {current_gesture} | AI: {comp_move}"
            game_state = "IDLE"

    # Obsługa animacji (interpolation)
    for anim in active_anims[:]:
        anim["t"] += time.dt
        lerp = min(anim["t"] / anim["time"], 1)
        s, target = anim["start"], anim["target"]
        anim["bone"].setHpr(tuple(s[i] + (target[i] - s[i]) * lerp for i in range(3)))
        if lerp >= 1: active_anims.remove(anim)

def input(key):
    global game_state, countdown
    if key == 'space' and game_state == "IDLE":
        game_state = "COUNTDOWN"
        countdown = 3

app.run()