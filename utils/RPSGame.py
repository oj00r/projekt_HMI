from ursina import *
from direct.actor.Actor import Actor
import cv2
import mediapipe as mp
import random
from PIL import Image
from utils.poses import RockPose, PapierPose, ScissorsPose

class RPSGame:
    def __init__(self, cam_index=0):
        # --- Ursina Setup ---
        # Naprawa błędu: Po prostu tworzymy instancję. 
        # Jeśli Ursina już działa w tle (co jest trudne w jednym procesie),
        # Panda3D obsłuży to wewnętrznie lub wyrzuci błąd, ale nie sprawdzamy .instance
        try:
            self.app = Ursina(vsync=True)
        except Exception as e:
            # Jeśli aplikacja już istnieje (np. przy ponownym uruchomieniu w tym samym procesie),
            # próbujemy podpiąć się pod istniejącą (to jest ryzykowne, ale jedyne wyjście bez restartu procesu)
            print(f"Ursina info: {e}")
            from ursina import application
            self.app = application.base

        # Ustawienia kamery 3D w grze
        camera.position = (5, 4.5, -7.5)
        camera.rotation = (48, -28, 0)
        
        # Reset sceny (ważne przy ponownym uruchomieniu)
        scene.clear()
        
        # Światło
        Entity(model='directional_light', rotation=(45, 45, 0))
        
        # Podgląd z kamery (UI)
        self.camera_view = Entity(model='quad', parent=camera.ui, scale=(0.4, 0.3), position=(0.6, -0.3))
        self.info_text = Text(text="SPACE - START", origin=(0,0), y=0.4, scale=2)

        # --- Kamera i Mediapipe ---
        self.cam_index = cam_index
        self.cap = cv2.VideoCapture(self.cam_index)
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            min_detection_confidence=0.6,
            min_tracking_confidence=0.6
        )

        # --- Model 3D (Actor) ---
        # Ścieżka musi być poprawna względem pliku main.py
        self.hand_actor = None
        try:
            # Próbujemy załadować model. Upewnij się, że plik istnieje w assets/reka/
            self.hand_actor = Actor("./assets/reka/hand2.glb") 
            self.hand_actor.reparentTo(scene)
            self.hand_actor.setScale(5)
            self.hand_actor.setPos(0, -10, 2)
        except Exception as e:
            print(f"BŁĄD ŁADOWANIA MODELU: {e}")
            print("Upewnij się, że plik './assets/reka/hand2.glb' istnieje.")

        self.bone_names = [
            "nadgarstek", "Przed_kciuk", "kciuk1", "kciuk2",
            "przed_wskazujacy", "wskazujacy1", "wskazujacy2", "wskazujacy3",
            "przed_srodkowy", "srodkowy1", "srodkowy2", "srodkowy3",
            "przed_serdeczny", "serdeczny1", "serdeczny2", "serdeczny3",
            "przed_maly", "maly1", "maly2", "maly3"
        ]
        
        # Kontrola kości - tylko jeśli model się załadował
        self.bones = {}
        if self.hand_actor:
            for name in self.bone_names:
                # controlJoint może zwrócić None jeśli kość nie istnieje w modelu
                joint = self.hand_actor.controlJoint(None, "modelRoot", name)
                if joint:
                    self.bones[name] = joint
        
        self.active_anims = []      

        
        # Upewnij się, że pozy są zdefiniowane zanim trafią do słownika
        self.Poses = {
            "rock": RockPose, 
            "paper": PapierPose, 
            "scissors": ScissorsPose
        }

        # --- Stan Gry ---
        self.game_state = "IDLE"
        self.countdown = 0
        self.current_gesture = "unknown"

    def classify_rps(self, hand_landmarks, handedness):
        lm = hand_landmarks.landmark
        
        # Logika: Palec jest "w górze" jeśli czubek (tip) jest wyżej (mniejsze Y) niż staw (pip)
        index_up  = lm[8].y  < lm[6].y
        middle_up = lm[12].y < lm[10].y
        ring_up   = lm[16].y < lm[14].y
        pinky_up  = lm[20].y < lm[18].y
        
        # Kciuk jest trudniejszy (zależy od ręki L/R i osi X)
        thumb_tip = lm[4]
        thumb_ip = lm[3]
        if handedness == "Right": # To zależy od lustrzanego odbicia
            thumb_up = thumb_tip.x > thumb_ip.x
        else:
            thumb_up = thumb_tip.x < thumb_ip.x

        # Prosta heurystyka
        fingers_up = [thumb_up, index_up, middle_up, ring_up, pinky_up]
        up_count = sum(fingers_up)

        if up_count <= 1: 
            return "rock"
        if up_count >= 4:
            return "paper"
        if index_up and middle_up and not ring_up and not pinky_up:
            return "scissors"
        
        return "unknown"

    def start_pose_anim(self, pose_name, duration=0.5):
        if pose_name not in self.Poses: return
        # Jeśli nie ma kości (błąd modelu), nie animujemy
        if not self.bones: return 

        pose_data = self.Poses[pose_name]
        for b_name, target_hpr in pose_data.items():
            if b_name in self.bones:
                self.active_anims.append({
                    "bone": self.bones[b_name],
                    "start": self.bones[b_name].getHpr(),
                    "target": target_hpr,
                    "time": duration,
                    "t": 0
                })

    def update(self):
        # 1. Odczyt z kamery
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.flip(frame, 1)
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                results = self.hands.process(rgb)
                
                self.current_gesture = "unknown"
                if results.multi_hand_landmarks:
                    land = results.multi_hand_landmarks[0]
                    # Pobieramy etykietę (Left/Right)
                    if results.multi_handedness:
                        hand_label = results.multi_handedness[0].classification[0].label
                        self.current_gesture = self.classify_rps(land, hand_label)
                
                # Aktualizacja tekstury w Ursina
                img_pil = Image.fromarray(cv2.resize(rgb, (400, 300)))
                self.camera_view.texture = Texture(img_pil)

        # 2. Logika gry
        if self.game_state == "COUNTDOWN":
            self.countdown -= time.dt
            self.info_text.text = str(max(0, int(self.countdown) + 1))
            if self.countdown <= 0:
                comp_move = random.choice(["rock", "paper", "scissors"])
                self.start_pose_anim(comp_move)
                self.info_text.text = f"Ty: {self.current_gesture} | AI: {comp_move}"
                self.game_state = "IDLE"

        # 3. Animacja kości (interpolacja liniowa)
        for anim in self.active_anims[:]:
            anim["t"] += time.dt
            lerp_val = min(anim["t"] / anim["time"], 1)
            s, target = anim["start"], anim["target"]
            
            new_hpr = (
                s[0] + (target[0] - s[0]) * lerp_val,
                s[1] + (target[1] - s[1]) * lerp_val,
                s[2] + (target[2] - s[2]) * lerp_val
            )
            
            anim["bone"].setHpr(new_hpr)
            if lerp_val >= 1:
                self.active_anims.remove(anim)

        # Wyjście awaryjne (ESC)
        if held_keys['escape']:
            self.close_game()

    def input(self, key):
        if key == "space" and self.game_state == "IDLE":
            self.game_state = "COUNTDOWN"
            self.countdown = 3

    def close_game(self):
        # Zwolnij kamerę przed wyjściem!
        if self.cap.isOpened():
            self.cap.release()
        
        # Wyjście z Ursina (zamyka proces)
        application.quit()

    def run(self):
        # Tworzymy Entity, które będzie "sercem" naszej logiki w pętli Ursina
        self.handler = Entity()
        self.handler.update = self.update
        self.handler.input = self.input
        
        # Uruchamiamy pętlę gry
        self.app.run()

if __name__ == "__main__":
    # Testowe uruchomienie bezpośrednio z pliku
    game = RPSGame(cam_index=2)
    game.run()