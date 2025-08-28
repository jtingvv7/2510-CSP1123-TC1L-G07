from flask import Flask, render_template, request, redirect, url_for
import smtplib, random

app = Flask(__name__)
app.secret_key = "yoursecretkey"

# store OTP temporarily
otp_storage = {}

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']

        # ✅ Only allow emails ending with @mmu.edu.my
        if not email.endswith("@mmu.student.edu.my"):
            return "❌ Only MMU student emails are allowed!"

        otp = str(random.randint(100000, 999999))
        otp_storage[email] = otp

        # Send OTP via Gmail SMTP
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login("yourgmail@gmail.com", "your-app-password")
        message = f"Your OTP is {otp}"
        server.sendmail("yourgmail@gmail.com", email, message)
        server.quit()

        return redirect(url_for('verify', email=email))
    return render_template('register.html')

@app.route('/verify/<email>', methods=['GET', 'POST'])
def verify(email):
    if request.method == 'POST':
        user_otp = request.form['otp']
        if otp_storage.get(email) == user_otp:
            return "✅ Email verified successfully!"
        else:
            return "❌ Invalid OTP"
    # Pass email into verify.html
    return render_template('verify.html', email=email)

if __name__ == "__main__":
    app.run(debug=True)
