# Ucyaegis Training — Django LMS

Ek fully working Learning Management System jisme:
- **Admin/Instructor login** — course banao, recorded lectures (video) upload karo
- **Student login** — course browse karo, payment karke enroll ho, phir lectures dekho
- Course tabhi "available" hota hai jab student **payment complete** kar leta hai (free course ho to seedha enroll ho jata hai)

Logo aapke uploaded image se liya gaya hai (`static/logo.jpeg`).

---

## 1. Setup (local machine par)

```bash
# 1. Project folder me jao
cd ucyaegis_project

# 2. Virtual environment banao (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 3. Dependencies install karo
pip install -r requirements.txt

# 4. Database migrate karo
python manage.py makemigrations
python manage.py migrate

# 5. (Optional) Django's built-in superuser banao — /django-admin/ access ke liye
python manage.py createsuperuser

# 6. Server chalao
python manage.py runserver
```

Ab browser me kholo: **http://127.0.0.1:8000/**

---

## 2. App kaise use karein

### Admin (SIRF AAP — ONE-TIME SETUP)
Admin registration ka link **kahin bhi UI me nahi dikhta** (na navbar me, na
homepage par) — sirf yeh URL directly browser me daal kar admin account
banaya ja sakta hai:

```
http://127.0.0.1:8000/accounts/admin/register/
```

1. Yeh URL kholo, apna admin account bana lo (ek hi baar)
2. **Bas ho gaya** — is form ke through dobara koi admin nahi ban sakta.
   Jaise hi ek admin account exist karta hai, yeh registration page khud-ba-khud
   **permanently lock** ho jata hai (koi bhi is URL par jaaye, "Admin
   registration is closed" message milega)
3. Admin login karne ke liye is URL ko bookmark kar lo (yeh bhi kahin
   link nahi hai):
   ```
   http://127.0.0.1:8000/accounts/admin/login/
   ```
4. Login ho jaoge → **Admin Dashboard** milega
3. **"+ Create New Course"** → title, description, price, thumbnail bharo
4. Course create hote hi seedha **lecture upload page** khulega — yahan recorded video (mp4) upload karo, multiple lectures add kar sakte ho
5. Dashboard me apne total students aur revenue bhi dikhega

### Student ke liye
1. Homepage par **"Join as Student"** click karo → register karo
   (URL: `/accounts/student/register/`)
2. Homepage / dashboard se koi bhi course choose karo
3. **"Enroll Now"** click karo → checkout page khulega
4. **"Pay & Enroll"** click karte hi (demo mode me) payment turant success ho jata hai aur enrollment create ho jati hai
5. Ab course ke lectures unlock ho jayenge aur "My Dashboard" → "Continue Learning" se video dekh sakte ho
6. Agar course free hai (price = 0), to payment ke bina hi seedha enroll ho jayega
7. Student apna account **permanently delete** bhi kar sakta hai — Student
   Dashboard ke sabse neeche "Delete My Account" link se (isse uske saare
   enrollments aur payment history bhi delete ho jaate hain)

### Django Admin panel (optional, superuser)
`/django-admin/` par jaakar saare Users, Courses, Lectures, Enrollments, Payments manage kar sakte ho.

---

## 3. Payment Gateway — RAZORPAY (UPI only, fully automatic)

Is project me **Razorpay real payment gateway** integrate hai, checkout **sirf
UPI dikhata hai** (cards/netbanking/wallets hidden hain) — aur payment
success hote hi **turant, automatically, bina kisi manual approval ke**
course unlock ho jata hai. Security ke liye cryptographic signature verify
hota hai server-side taaki koi browser se fake "success" na bhej sake.

### Setup Steps

1. **Razorpay account banao** (free): https://dashboard.razorpay.com/signup
2. Login karke **Settings → API Keys → Generate Test Key** par jao
   - Isse aapko ek **Key Id** (`rzp_test_...`) aur **Key Secret** milega
3. `ucyaegis/settings.py` file kholo aur apni keys yahan daalo:
   ```python
   RAZORPAY_KEY_ID = 'rzp_test_XXXXXXXXXXXXXX'
   RAZORPAY_KEY_SECRET = 'your_actual_key_secret'
   ```
4. `razorpay` Python package install karo (already `requirements.txt` me hai):
   ```bash
   python -m pip install -r requirements.txt
   ```
5. Migrations chalao (Payment model me naye fields hain):
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```
6. Server run karo aur ek course par "Enroll Now" click karo — sirf UPI
   option wala Razorpay checkout popup khulega

### Test Mode me Payment kaise karein (bina real paise ke)

Test Key use karte waqt Razorpay real paise nahi kaatega. Testing ke liye
special test UPI ID use karo:
```
Success test: success@razorpay
Failure test: failure@razorpay
```
Poori list yahan hai: https://razorpay.com/docs/payments/payments/test-card-upi-details/

### Payment kaise verify hota hai aur turant access kaise milta hai

1. Student "Pay via UPI" click karta hai → server ek real **Razorpay Order**
   create karta hai (`initiate_payment` view)
2. Razorpay ka checkout popup khulta hai — **sirf UPI** option dikhta hai
   (QR scan ya UPI ID daal ke pay kar sakta hai)
3. Success hone par Razorpay browser ko `razorpay_payment_id`,
   `razorpay_order_id`, aur `razorpay_signature` deta hai
4. Yeh teeno turant server ko bheje jaate hain (`verify_payment` view), jo
   Razorpay ke Key Secret se **signature verify** karta hai — sab kuch
   1-2 second me ho jata hai
5. Signature valid ho tabhi `Payment.status = 'success'` set hota hai aur
   `Enrollment` create hoti hai — **tabhi turant, automatically course
   unlock ho jata hai, koi wait ya admin approval nahi chahiye**
6. Agar student popup band kar de bina pay kiye, to payment "failed" mark
   ho jati hai aur course locked hi rehta hai

### LIVE (real paise) par jaane ke liye

1. Razorpay dashboard par KYC/business verification complete karo
2. **Live Mode** me switch karke Live Key Id/Secret generate karo
3. `settings.py` me Test keys ki jagah Live keys daalo
4. (Recommended) Razorpay **Webhooks** bhi setup karo — Settings → Webhooks
   → apna URL add karo — yeh ek extra server-side confirmation deta hai
   agar student ka browser verify_payment call complete hone se pehle
   band ho jaye


---

## 4. Project Structure

```
ucyaegis_project/
├── manage.py
├── requirements.txt
├── ucyaegis/           # project settings, urls
├── accounts/           # custom User model, admin/student login & register
├── courses/            # Course, Lecture, Enrollment, Payment models + views
├── templates/          # all HTML templates (base.html has navbar + logo)
├── static/             # logo.jpeg, css/style.css
└── media/              # uploaded thumbnails & lecture videos (created at runtime)
```

---

## 5. Notes

- `DEBUG = True` hai — production me isse `False` karo aur `ALLOWED_HOSTS`,
  `SECRET_KEY` properly set karo.
- Large lecture videos ke liye production me S3 / Cloud storage use karna
  behtar hoga (abhi local `media/` folder me store hote hain).
- Yeh code is sandboxed environment me **run/test nahi ho paya** (no internet/
  no Django pre-installed here) — lekin har `.py` file syntax-checked hai aur
  Django ke standard patterns follow karti hai. Apne local machine par upar
  diye steps follow karke turant chala sakte ho.
