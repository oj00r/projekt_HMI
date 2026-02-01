from ursina import *
from direct.actor.Actor import Actor
import cv2
import mediapipe as mp
import random
import pickle
import numpy as np
from PIL import Image

# Importujemy pozy z zewnętrznego pliku
try:
    # Próba 1: Import absolutny (gdy uruchamiamy przez main.py jako moduł)
    from utils.poses import RockPose, PapierPose, ScissorsPose
except ImportError:
    try:
        # Próba 2: Import lokalny (gdy uruchamiamy RPSGame.py bezpośrednio)
        # Ponieważ RPSGame i poses są w tym samym folderze, czasem trzeba tak:
        from poses import RockPose, PapierPose, ScissorsPose
    except ImportError:
        print("BŁĄD KRYTYCZNY: Nie udało się załadować pliku poses.py!")

class RPSGame:
    def __init__(self, cam_index=0):
        # --- Ursina Setup ---
        try:
            self.app = Ursina(vsync=True)
        except Exception as e:
            print(f"Ursina info: {e}")
            from ursina import application
            self.app = application.base

        camera.position = (5, 4.5, -7.5)
        camera.rotation = (48, -28, 0)
        scene.clear()
        
        Entity(model='directional_light', rotation=(45, 45, 0))
        
        # Podgląd z kamery
        self.camera_view = Entity(model='quad', parent=camera.ui, scale=(0.4, 0.3), position=(0.6, -0.3))
        
        # Tekst informacyjny (środek)
        self.info_text = Text(text="SPACE - START", origin=(0,0), y=0.4, scale=2, color=color.white)

        # --- NOWE: Licznik punktów (Lewy górny róg) ---
        self.player_score = 0
        self.ai_score = 0
        self.score_text = Text(
            text=f"TY: {self.player_score} | Komputer: {self.ai_score}", 
            position=(-0.85, 0.45), 
            scale=1.5, 
            color=color.white
        )

        # --- Ładowanie Modelu AI ---
        self.model = None
        try:
            # Uwaga: Upewnij się, że ścieżka jest poprawna
            model_dict = pickle.load(open('./model/model.p', 'rb')) 
            self.model = model_dict['model']
            print("Sukces: Model AI załadowany!")
        except Exception as e:
            print(f"UWAGA: Nie znaleziono model.p lub błąd ładowania: {e}")

        self.labels_dict = {0: 'paper', 1: 'rock', 2: 'scissors'}

        # --- Kamera i Mediapipe (OPTYMALIZACJA) ---
        self.cam_index = cam_index
        self.cap = cv2.VideoCapture(self.cam_index)
        
        # 1. Wymuszamy niską rozdzielczość na poziomie kamery
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
        
        self.mp_hands = mp.solutions.hands
        
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,
            model_complexity=0,       # 2. Tryb Lite (szybki)
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            static_image_mode=False
        )

        # --- Model 3D ---
        self.hand_actor = None
        try:
            self.hand_actor = Actor("../assets/reka/hand2.glb") 
            self.hand_actor.reparentTo(scene)
            self.hand_actor.setScale(5)
            self.hand_actor.setPos(0, -10, 2)
        except:
            print("Brak modelu 3D ręki.")

        self.bone_names = [
            "nadgarstek", "Przed_kciuk", "kciuk1", "kciuk2",
            "przed_wskazujacy", "wskazujacy1", "wskazujacy2", "wskazujacy3",
            "przed_srodkowy", "srodkowy1", "srodkowy2", "srodkowy3",
            "przed_serdeczny", "serdeczny1", "serdeczny2", "serdeczny3",
            "przed_maly", "maly1", "maly2", "maly3"
        ]
        
        self.bones = {}
        if self.hand_actor:
            for name in self.bone_names:
                joint = self.hand_actor.controlJoint(None, "modelRoot", name)
                if joint:
                    self.bones[name] = joint
        
        self.active_anims = []      
        self.Poses = {"rock": RockPose, "paper": PapierPose, "scissors": ScissorsPose}

        self.game_state = "IDLE"
        self.countdown = 0
        self.current_gesture = "unknown"

    # Zapasowa funkcja (heurystyka)
    def classify_heuristic(self, hand_landmarks, handedness):
        lm = hand_landmarks.landmark
        index_up  = lm[8].y  < lm[6].y
        middle_up = lm[12].y < lm[10].y
        ring_up   = lm[16].y < lm[14].y
        pinky_up  = lm[20].y < lm[18].y
        thumb_tip = lm[4]
        thumb_ip = lm[3]
        
        if handedness == "Right": thumb_up = thumb_tip.x > thumb_ip.x
        else: thumb_up = thumb_tip.x < thumb_ip.x

        up_count = sum([thumb_up, index_up, middle_up, ring_up, pinky_up])
        if up_count <= 1: return "rock"
        if up_count >= 4: return "paper"
        if index_up and middle_up and not ring_up and not pinky_up: return "scissors"
        return "unknown"

    def start_pose_anim(self, pose_name, duration=0.5):
        if pose_name not in self.Poses or not self.bones: return
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
        if self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # 3. Skalowanie w dół dla pewności (oszczędza CPU przy obracaniu i konwersji)
                frame_small = cv2.resize(frame, (320, 240))
                
                frame_flipped = cv2.flip(frame_small, 1)
                frame_rgb = cv2.cvtColor(frame_flipped, cv2.COLOR_BGR2RGB)
                
                results = self.hands.process(frame_rgb)
                
                self.current_gesture = "unknown"
                
                if results.multi_hand_landmarks:
                    hand_landmarks = results.multi_hand_landmarks[0]
                    
                    if self.model:
                        try:
                            data_aux = []
                            x_ = []
                            y_ = []

                            for lm in hand_landmarks.landmark:
                                x_.append(lm.x)
                                y_.append(lm.y)

                            min_x = min(x_)
                            min_y = min(y_)
                            
                            for lm in hand_landmarks.landmark:
                                data_aux.append(lm.x - min_x)
                                data_aux.append(lm.y - min_y)

                            prediction = self.model.predict([np.asarray(data_aux)])
                            prediction_idx = int(prediction[0])
                            
                            self.current_gesture = self.labels_dict.get(prediction_idx, "unknown")
                            
                        except Exception as e:
                            pass
                    else:
                        if results.multi_handedness:
                            hand_lbl = results.multi_handedness[0].classification[0].label
                            self.current_gesture = self.classify_heuristic(hand_landmarks, hand_lbl)
                
                # Wyświetlanie (już małego obrazka, więc jest wydajnie)
                img_pil = Image.fromarray(frame_rgb)
                self.camera_view.texture = Texture(img_pil)

        # --- Logika Rozgrywki ---
        if self.game_state == "COUNTDOWN":
            self.countdown -= time.dt
            if self.countdown > 0:
                self.info_text.text = str(int(self.countdown) + 1)
            else:
                # KONIEC ODLICZANIA - ROZSTRZYGNIĘCIE
                comp_move = random.choice(["rock", "paper", "scissors"])
                self.start_pose_anim(comp_move)
                
                g = self.current_gesture
                c = comp_move
                
                if g == "unknown":
                    result_msg = "Nie widzę ręki!"
                    self.info_text.color = color.white
                elif g == c:
                    result_msg = "REMIS!"
                    self.info_text.color = color.white
                elif (g == "rock" and c == "scissors") or \
                     (g == "paper" and c == "rock") or \
                     (g == "scissors" and c == "paper"):
                    result_msg = "WYGRAŁEŚ! :)"
                    self.info_text.color = color.green
                    # --- NOWE: Dodajemy punkt graczowi ---
                    self.player_score += 1
                else:
                    result_msg = "PRZEGRAŁEŚ :("
                    self.info_text.color = color.red
                    # --- NOWE: Dodajemy punkt Komputer ---
                    self.ai_score += 1

                # Aktualizujemy tekst wyniku i licznika punktów
                self.info_text.text = f"Ty: {g.upper()} \nKomputer: {c.upper()}\n{result_msg}"
                self.score_text.text = f"TY: {self.player_score} | Komputer: {self.ai_score}"
                
                self.game_state = "RESULT"
                self.countdown = 2.0

        elif self.game_state == "RESULT":
            self.countdown -= time.dt
            if self.countdown <= 0:
                self.game_state = "IDLE"
                self.info_text.text = "SPACE - START"
                self.info_text.color = color.white

        # Animacja kości
        for anim in self.active_anims[:]:
            anim["t"] += time.dt
            lerp_val = min(anim["t"] / anim["time"], 1)
            s, target = anim["start"], anim["target"]
            new_hpr = tuple(s[i] + (target[i] - s[i]) * lerp_val for i in range(3))
            anim["bone"].setHpr(new_hpr)
            if lerp_val >= 1:
                self.active_anims.remove(anim)

        if held_keys['escape']:
            self.close_game()

    def input(self, key):
        if key == "space" and self.game_state == "IDLE":
            self.game_state = "COUNTDOWN"
            self.info_text.color = color.yellow
            self.countdown = 3

    def close_game(self):
        if self.cap.isOpened():
            self.cap.release()
        application.quit()

    def run(self):
        self.handler = Entity()
        self.handler.update = self.update
        self.handler.input = self.input
        self.app.run()

if __name__ == "__main__":
    # Testowe uruchomienie bezpośrednio z pliku
    game = RPSGame(cam_index=2)
    game.run()