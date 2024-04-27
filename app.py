from flask import Flask,render_template,request,session,redirect,send_from_directory,Response,jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import os
import sqlite3
import datetime
import cv2
import numpy as np
import pickle
import mediapipe as mp
import logging

global pred
pred=""
mp_drawing = mp.solutions.drawing_utils
mp_pose = mp.solutions.pose

global exer_name
global count_n
global flash_flag
flash_flag=0
pickle_in = open("studentmodel.pickel", "rb")
model = pickle.load(pickle_in)

def calculate_angle(a,b,c):
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle >180.0:
        angle = 360-angle
        
    return angle 


app = Flask(__name__)
logging.basicConfig(filename='error.log', level=logging.ERROR)
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key="personaltrainer"
with sqlite3.connect('users.db') as db:
    c = db.cursor()

c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT,firstname TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password TEXT NOT NULL,lastname TEXT NOT NULL,height TEXT NULL,weight TEXT NOT NULL,age Text NOT NULL,city Text NOT NULL,bio Text NOT NULL,image Text NOT NULL, hp Text NOT NULL,bs Text NOT NULL,bc Text NOT NULL,bp Text NOT NULL);')
db.commit()
db.close()

def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@app.route('/')
@app.route('/home')
def home():
	return render_template('home.html')

@app.route('/assets/imgs/<filename>')
def serve_image(filename):
    root_dir = os.path.dirname(os.path.abspath(__file__))
    image_path = os.path.join(root_dir, 'assets')
    print(image_path)
    return send_from_directory(image_path, filename)

@app.route('/login', methods=['POST','GET'])
def login():
    if request.method == 'POST':
        username = request.form['email']
        password = request.form['password']
        print(username,password)

        conn = sqlite3.connect('users.db')
        c = conn.cursor()

        c.execute('SELECT * FROM users WHERE email=?', (username,))
        user = c.fetchone()

        if not user:
            print("no user")
            return render_template('login.html', error='Invalid username or password')
        print(user)
        if user[4]!=password:
            print("wrong password")
            return render_template('login.html', error='Invalid username or password')

        session['firstname'] = user[1]
        session['email'] = user[2]
        session['lastname'] = user[4]
        session['height'] = user[5]
        session['weight'] = user[6]
        session['age'] = user[7]
        session['city'] = user[8]
        session['bio'] = user[9]
        session['image'] = user[10]
        session['hp'] = user[11]
        session['bs'] = user[12]
        session['bc'] = user[13]
        session['bp'] = user[14]
        return redirect('/profile')

    return render_template('login.html')

@app.route('/register', methods=['POST','GET'])
def register():
    if request.method == 'POST':
        firstname = request.form['first-name']
        lastname = request.form['last-name']
        password = request.form['password']
        email = request.form['email']
        height = request.form['height']
        weight = request.form['weight']
        age = request.form['age']
        city = request.form['city']
        bio = request.form['bio']
        hp = request.form['hp']
        bs = request.form['bs']
        bc = request.form['bc']
        bp = request.form['bp']
        imagefile = request.files['file']
        print(firstname, password,lastname,height,weight,age,city,bio,imagefile)
        errors = []
        if len(firstname) < 3:
            errors.append("Name should be at least 3 characters long.")
        if len(password) < 6:
            errors.append("Password should be at least 6 characters long.")
        if int(height) <= 0 or int(weight) <= 0:
            errors.append("Height and weight should be greater than zero.")
        if imagefile and allowed_file(imagefile.filename):
                filename = imagefile.filename
                imagefile.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        else:
            errors.append("Invalid file format! Allowed formats: png, jpg, jpeg, gif")
        if errors:
            return render_template('register.html', errors=errors)
        
            
        else:
            conn = sqlite3.connect('users.db')
            c = conn.cursor()

            hashed_password = generate_password_hash(password)

            c.execute('SELECT * FROM users WHERE email=?', (email,))
            if c.fetchone():
                return render_template('register.html', error='email already exists')

            c.execute('INSERT INTO users (firstname,email, password,lastname,height,weight,age,city,bio,image, hp,bs,bc,bp ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?,?,?)', (firstname,email, hashed_password,lastname,height,weight,age,city,bio,filename, hp,bs,bc,bp))
            conn.commit()
            return redirect('/login')
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/home')

@app.route('/profile')
def profile():
    fname = session['firstname']+" "+session['lastname']
    height = session['height']
    weight =session['weight']
    age =session['age']
    bio=session['bio']
    hp=session['hp']
    bs=session['bs']
    bc=session['bc']
    bp=session['bp']
    bmi=(int(weight)/(int(height)*int(height)/10000))

    day_time=["Breakfast","Lunch","Snack","Dinner"]

    monday1=["2 Idli (brown rice), sambhar/ 2 whole eggs + toast","Whole grain roti + mixed vegetable / chicken","5 almonds + unsweetened tea or coffee","Soup with sauteed veg"]
    tuesday1=["Atta or moong dal chilla / scrambled eggs + toast","Brown rice + gravy sabzi or dal","Fruits + unsweetened tea or coffee","Porridge with salad"]
    wednesday1=["Porridge / fruits with milk / omelette","Whole grain roti + paneer / vegetable salad","2 dates + unsweetened tea or coffee","2 dates + unsweetened tea or coffee"]
    thursday1=["Oats and yogurt/vegetable omelet","Whole grain roti + vegetables / sauteed chicken roti wrap","5 almonds + 5 walnuts + buttermilk","Brown rice + masala chana/chicken"]
    friday1=["Daliya / French toast","Sambar and rice","5 almonds + 2 dates + unsweetened tea or coffee","Vegetable pulao / chicken pulao + curd"]
    saturday1=["Parathas / egg + roti","Whole grain roti + gravy sabzi/chicken curry with quinoa","Fruits + unsweetened tea or coffee","Dal ka chilla with grilled paneer or fish"]
    sunday1=["Oats with milk and fruits","Whole grain roti + sabzi / soup + salad","Yogurt with fruits","Tandoori paneer / chicken/ fish"]

    monday3=["3 onion stuffed parantha + 1 cup curd + 3 cashews + 4 almonds + 2 walnuts","1 cup mango shake","1 cup moong dal/ chicken curry + 1 cup potato and caulifllower vegetable + 3 chapatti + 1/2 cup rice + salad","1 cup pomegranate juice + 2 butter toasted bread","1 cup beans potato vegetable + 3 chapatti + salad"]
    tuesday3=["3 paneer stuffed besan cheela + green chutney + 1 cup curd + 3 cashews + 4 almonds + 2 walnuts","1 apple smoothie with maple syrup","1 cup masoor dal + 1 cup calocasia + 3 chapatti + 1/2 cup rice + 1 cup low curd + salad","1 cup tomato soup with bread crumbs + 1 cup aloo chaat","1 cup carrot peas vegetable +3 chapatti + salad"]
    wednesday3=["1.5 cup vegetable bread upma + 1 cup milk + 3 cashews + 4 almonds + 2 walnuts","Meal-1 cup ripe banana with 2 tsp ghee","1 cup rajma curry + 1 cup spinach potato + 3 chapatti + 1/2 cup rice + salad","1 cup vegetable juice + 1 cup upma","1.5 cup parwal vegetable + 3 chapatti + salad"]
    thursday3=["2 cucmber potato sandwich + 1 tsp green chutney + 1 orange juice + 3 cshews + 2 walnuts + 4 almonds","1 cup buttermilk + 1 cup sweet potato chaat","1 cup white chana/ fish curry + 3 chapatti + 1/2 cup rice + salad","1 cup almond milk + banana","1 cup cauliflower potato vegetable + 3 chapatti + salad"]
    friday3=["2 cup vegetable poha + 1 cup curd + 3 cashews + 4 almonds + 2 walnuts","2 cups watermelon juice","1 cup chana dal + 1 cup bhindi vegetable + 3 chapatti + 1/2 cup rice + salad","1 cup sprouts salad + 2 potato cheela + green chutney","1 cup peas mushroom vegetable + 3 chapatti + salad"]
    saturday3=["3 vegetable suji cheela + 1 cup strawberry shake + 4 cashews + 4 almonds + 3 walnuts","1 cup coconut water + 1 cup pomegrate","1 cup mix dal + 1 cup soybean curry + 3 chapatti + 1/2 cup curd + salad","1 cup fruit salad + 4 pc vegetable cutlets + green chutney","1 cup karela vegetable + 3 chaptti + salad"]
    sunday3=["2 egg brown bread sandwich + green chutney + 1 cup milk + 3 cashews + 4 almonds + 2 walnuts","1 cup banana shake","1 cup arhar dal + 1 cup potato curry + 3 chapatti + 1/2 cup rice + 1/2 cup low fat curd + salad","1 cup strawberry smoothie + 1 cup vegetable poha","1.5 cup chicken curry + 3 chapatti + salad"]

    monday5=["smoked salmon with 2 eggs and spinach","beetroot and fetasalad","fillet steak and mushrooom"]
    tuesday5=["greek yogurt with raspberries or blueberries and 1l2 banana","cajun chicken breast with brocoli,spring greens and soy","king prawn stir fry with baby sweetcorn,snow peas and brocoli"]
    wednesday5=["protein shake with almond or coconut milk","spinach and roast veg cauliflower,pepper and chickpeas","seabass with asparagus and roasted tomatoes"]
    thursday5=["2 egg 1 white omlet with mushrooms and feta cheese","tuna nicose salad with balasamic dressing","chicken breast ewith roasted peppers and onions"]
    friday5=["overnight oats 50g with almond and berries ","roasted halloumi peppers and tomatoes with rocket","steamed halibut with sweet potato mash and brocoli"]
    saturday5=["baked avacado with eggs and chilli flakes","salmon fillet with stir fried green veg","chicken with peppers,onions and tomatoes"]
    sunday5=["protein shake with almond or coconut milk","roast chicken,potatoes,carrots,brocoli","greek yogurt,20g cashewnut and berries"]

    if bmi>25:
        mon=zip(day_time,monday1)
        tue=zip(day_time,tuesday1)
        wed=zip(day_time,wednesday1)
        thu=zip(day_time,thursday1)
        fri=zip(day_time,friday1)
        sat=zip(day_time,saturday1)
        sun=zip(day_time,sunday1)
        res="Over Weight"
        
    elif bmi<18:
        mon=zip(day_time,monday3)
        tue=zip(day_time,tuesday3)
        wed=zip(day_time,wednesday3)
        thu=zip(day_time,thursday3)
        fri=zip(day_time,friday3)
        sat=zip(day_time,saturday3)
        sun=zip(day_time,sunday3) 
        res="Under Weight"   
    
    else:
        mon=zip(day_time,monday5)
        tue=zip(day_time,tuesday5)
        wed=zip(day_time,wednesday5)
        thu=zip(day_time,thursday5)
        fri=zip(day_time,friday5)
        sat=zip(day_time,saturday5)
        sun=zip(day_time,sunday5)
        res="Normal"
    x = datetime.datetime.now()
    print(x.strftime("%b"))
    imgn=os.path.join("static/uploads",session['image'])
    print(imgn)
    return render_template('profile.html',imgname= imgn,fname=fname,bio=bio,height=height,weight=weight,age=age,bmi=bmi,monday=mon,tuesday=tue,wednesday=wed,thursday=thu,friday=fri,saturday=sat,sunday=sun,res=res, hp=hp,bs=bs,bc=bc,bp=bp)

@app.route('/stop')
def stop():
    return redirect('/profile')


def process_frames_exercise1():
    req_pose="Jumping Jack"
    global pred
    global exer_name
    global count_n
    global flash_flag
    flash_flag=0
    cap = cv2.VideoCapture(0)
    count = 0
    frameloc=[]
    pred=''
    count1=0
    count2=0
    count3=0
    count4=0
    count5=0
    count6=0
    t=50
    done=False
    with mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5) as pose:
        while True:
            th=5
            ret, frame = cap.read()
            if not ret or done:
                return redirect('/login')
            image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image.flags.writeable = False
            results = pose.process(image)
            image.flags.writeable = True
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            try:
                landmarks = results.pose_landmarks.landmark

                
                if count1<th:
                    req_pose="Jumping Jack"
                    a = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    b = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    c = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                    angle = calculate_angle(a, b, c)

                    a1 = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
                    b1 = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
                    c1 = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]

                    angle1 = calculate_angle(a1, b1, c1)

                    cv2.putText(image, str(angle),tuple(np.multiply(b, [640, 480]).astype(int)),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

                    if angle <89 and angle1<89:
                        flag = 1
                    if angle >95 and flag==1 and angle1>95:
                        flag=0
                        count1 +=1
                        print(count1)
                        if angle <100 or angle1<100:
                            jj=1
                            cv2.putText(image, "Please widen your legs",(10,100),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
                            flash_flag="Please widen your legs"
                    count=count1
                    if jj!=0 and jj < 10:
                        cv2.putText(image, "Please widen your legs",(10,100),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
                        flash_flag="Please widen your legs"
                        jj=jj+1
                    elif jj>=10:
                        jj=0
                    
                elif count2<th:
                    
                    if count2==0:
                        flash_flag=1
                        cv2.putText(image, "Right leg rise",(100,100),cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2, cv2.LINE_AA)
                    else:
                        flash_flag=0
                    req_pose="Right Leg Rise"
                    a = [landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    b = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    c = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                    angle = calculate_angle(a, b, c)

                    cv2.putText(image, str(angle),tuple(np.multiply(b, [640, 480]).astype(int)),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

                    if angle <100:
                        flag = 1
                    if angle >110 and flag==1:
                        flag=0
                        count2 +=1
                        if angle <115:
                            cv2.putText(image, "Lift your right leg more",(10,100),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
                            flash_flag="Lift your right leg more"
                    count=count2
                elif count3<th:
                    
                    if count3==0:
                        flash_flag=1
                        cv2.putText(image, "Left leg rise",(100,100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2, cv2.LINE_AA)
                    else:
                        flash_flag=0
                    req_pose="Left Leg Rise"
                    angle = calculate_angle(a, b, c)

                    a = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y]
                    b = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y]
                    c = [landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].x,landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]

                    angle = calculate_angle(a, b, c)

                    #cv2.putText(image, str(angle),tuple(np.multiply(b, [640, 480]).astype(int)),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2, cv2.LINE_AA)

                    if angle <100:
                        flag = 1
                    if angle >110 and flag==1:
                        if angle <120:
                            cv2.putText(image, "Lift your left leg more",(10,100),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2, cv2.LINE_AA)
                            flash_flag="Lift your left leg more"
                        flag=0
                        count3 +=1
                    count=count3
                elif count4<th:
                    if count4==0:
                        flash_flag=1
                        cv2.putText(image, "Left High Knee rise",(100,100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2, cv2.LINE_AA)
                    else:
                        flash_flag=0
                    req_pose="Left High Knee Rise"
                    if landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y <landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y:
                        flag = 1
                    if landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y >landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y and flag==1:
                        flag=0
                        count4 +=1
                    count=count4
                    
                elif count5<th:
                    
                    if count5==0:
                        flash_flag=1
                        cv2.putText(image, "Right High Knee rise",(100,100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2, cv2.LINE_AA)
                    else:
                        flash_flag=0
                    req_pose="Right High Knee Rise"
                    if landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y <landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y:
                        flag = 1
                    if landmarks[mp_pose.PoseLandmark.RIGHT_KNEE.value].y >landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value].y and flag==1:
                        flag=0
                        count5 +=1
                    count=count5

                elif count6<th:
                    
                    if count6<=1:
                        flash_flag=1
                        cv2.putText(image, "Side Bend",(10,100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 0), 2, cv2.LINE_AA)
                    else:
                        flash_flag=0
                    req_pose="Side Bend"
                    if landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y >landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y and landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x <landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x:
                        flag = 1
                    if landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].y >landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].y and  landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW.value].x >landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value].x and flag==1:
                        flag=0
                        count6 +=1
                    count=count6
                    if count6>=th:
                        flash_flag=2
                        cv2.putText(image, "Finished",(10,100),cv2.FONT_HERSHEY_SIMPLEX, 2, (0, 0, 255), 2, cv2.LINE_AA)
                    else:
                        flash_flag=0
                    
            except:
                pass
            #print(count)
            exer_name=req_pose
            count_n=count
            #cv2.putText(image, 'Count :'+str(count), (15,12),cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,0), 1, cv2.LINE_AA)
            #cv2.putText(image,"Current Exercise: " +str(req_pose), (60,450), cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 2, cv2.LINE_AA)

            mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)  
            frame = cv2.resize(image, (920, 640))
            ret, jpeg = cv2.imencode('.jpg', frame)
            frame = jpeg.tobytes()
            yield (b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        

@app.route('/video_feed_exercise1')
def video_feed_exercise():
    return Response(process_frames_exercise1(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/fetch_data')
def fetch_data():
    global exer_name
    global count_n
    global flash_flag
    #print(exer_name)
    data = {'letter':exer_name,'word':count_n,'flag':flash_flag}
    return jsonify(data)

def preprocess_frame(frame):
    processed_frame = frame 
    #processed_frame = np.expand_dims(processed_frame, axis=0)

    return processed_frame
@app.route('/webcam')
def webcam():
    print("webcam")
    return render_template('index5.html')

@app.route('/webcam2')
def webcam2():
    return render_template('index4.html')

@app.route('/fetch_letter')
def fetch_letter():
    global pred

    letter = pred

    return letter

@app.route('/diet')
def diet():
	return render_template('diet.html')

if __name__ == '__main__':
    app.run(debug=True)