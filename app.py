from flask import Flask, request, redirect, render_template, session, url_for, jsonify
import pandas as pd
import os
from datetime import datetime
from itsdangerous import URLSafeTimedSerializer
import shutil

app = Flask(__name__)
app.secret_key = 'a_very_secret_key_123!@#'  # Required for session handling

s = URLSafeTimedSerializer(app.secret_key)


ORIGINAL_USER_FILE = 'users.xlsx'
ORIGINAL_TABLE_FILE = 'tables.xlsx'
ORIGINAL_FOODMENU_FILE = 'foodmenu.xlsx'
ORIGINAL_RESERVATIONS_FILE = 'reservations.xlsx'
ORIGINAL_FINAL_CONFIRMATION_FILE = 'final_confirmations.xlsx'

USER_FILE = '/tmp/users.xlsx'
TABLE_FILE = '/tmp/tables.xlsx'
FOODMENU_FILE = '/tmp/foodmenu.xlsx'
RESERVATIONS_FILE = '/tmp/reservations.xlsx'
FINAL_CONFIRMATION_FILE = '/tmp/final_confirmations.xlsx'

if not os.path.exists(USER_FILE):
    shutil.copy(ORIGINAL_USER_FILE, USER_FILE)

if not os.path.exists(TABLE_FILE):
    shutil.copy(ORIGINAL_TABLE_FILE, TABLE_FILE)

if not os.path.exists(FOODMENU_FILE):
    shutil.copy(ORIGINAL_FOODMENU_FILE, FOODMENU_FILE)

if not os.path.exists(RESERVATIONS_FILE):
    shutil.copy(ORIGINAL_RESERVATIONS_FILE, RESERVATIONS_FILE)
    
if not os.path.exists(FINAL_CONFIRMATION_FILE):
    shutil.copy(ORIGINAL_FINAL_CONFIRMATION_FILE, FINAL_CONFIRMATION_FILE)

# Ensure necessary files exist
for file_path, columns in [
    (USER_FILE, ['email','username', 'password']),
    (TABLE_FILE, ['Table ID', 'Capacity', 'Availability']),
    (FOODMENU_FILE, ['Food Item', 'Price']),
    (RESERVATIONS_FILE, ['Name', 'Mobile', 'Table ID', 'Start Time', 'End Time'])
]:
    if not os.path.exists(file_path):
        pd.DataFrame(columns=columns).to_excel(file_path, index=False)

@app.route("/")
def home():
    #return redirect("/index")
    return render_template("index.html")
    
@app.route('/health')
def health_check():
    return jsonify({'Status': '200'})

@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        df = pd.read_excel(USER_FILE)
        user_match = df[(df["username"] == username) & (df["password"] == password)]

        if not user_match.empty:
            session["username"] = username  # <- set session properly
            return redirect("/dashboard")
        else:
            message = "<p style='color:red;'>Invalid username or password</p>"

    return render_template("login.html", message=message)

@app.route("/register", methods=["GET", "POST"])
def register():
    message = ""
    if request.method == "POST":
        email=request.form["email"]
        username = request.form["username"]
        #email=request.form["email"]
        password = request.form["password"]
        df = pd.read_excel(USER_FILE)

        if username in df["username"].values:
            message = "<p style='color:red;'>Username already exists</p>"
        else:
            new_user = pd.DataFrame([{
                'email': email,
                'username': username,
                'password': password
            }])
            df = pd.concat([df, new_user], ignore_index=True)
            df.to_excel(USER_FILE, index=False)
            
            return redirect("/login")

    return render_template("register.html", message=message)


@app.route("/dashboard")
def dashboard():
    #username = request.args.get("username", "Guest")
    username = session.get("username","Guest")
    session["username"] = username  # Save username in session
        
    # Enable button only if reservation exists in session
    can_order = 'reservation' in session and session['reservation']
    return render_template("dashboard.html", username=username, can_order=can_order)


@app.route("/reserve", methods=["GET", "POST"])
def reserve():
    df = pd.read_excel(TABLE_FILE)

    # Auto-release expired reservations
    if os.path.exists(RESERVATIONS_FILE):
        reservations = pd.read_excel(RESERVATIONS_FILE)
        now = datetime.now()
        still_reserved = []

        for _, row in reservations.iterrows():
            end_time = pd.to_datetime(row["End Time"])
            if end_time > now:
                still_reserved.append(row)
            else:
                df.loc[df["Table ID"] == row["Table ID"], "Availability"] = "Available"

        pd.DataFrame(still_reserved).to_excel(RESERVATIONS_FILE, index=False)
        df.to_excel(TABLE_FILE, index=False)

    if request.method == "POST":
        name = request.form.get("name")
        mobile = request.form.get("mobile")
        start_time = request.form.get("start_time")
        end_time = request.form.get("end_time")
        selected = request.form.getlist("selected_tables")
        username = session.get("username")

        reserved_tables = []

        for table_id in selected:
            table_id = int(table_id)
            if df.loc[df["Table ID"] == table_id, "Availability"].values[0] == "Available":
                df.loc[df["Table ID"] == table_id, "Availability"] = "Reserved"
                reserved_tables.append(table_id)

        if reserved_tables:
            df.to_excel(TABLE_FILE, index=False)

            new_reservations = pd.DataFrame([{
                "Username": username,
                "Name": name,
                "Mobile": mobile,
                "Table ID": tid,
                "Start Time": pd.to_datetime(start_time),
                "End Time": pd.to_datetime(end_time)
            } for tid in reserved_tables])

            # ✅ Load existing reservation file properly
            if os.path.exists(RESERVATIONS_FILE):
                try:
                    existing = pd.read_excel(RESERVATIONS_FILE)
                    combined = pd.concat([existing, new_reservations], ignore_index=True)
                except Exception as e:
                    print("Error reading RESERVATIONS_FILE:", e)
                    combined = new_reservations  # fallback to just new
            else:
                combined = new_reservations

            # ✅ Save the *combined* DataFrame
            combined.to_excel(RESERVATIONS_FILE, index=False)

            session['reservation'] = {
                'username': username,
                'name': name,
                'mobile': mobile,
                'tables': reserved_tables,
                'start_time': start_time,
                'end_time': end_time
            }

            action = request.form.get("action")
            if action == "reserve_and_order":
                return redirect("/menu")
            else:
                return render_template("confirmation.html",
                    name=name,
                    mobile=mobile,
                    tables=reserved_tables,
                    start_time=start_time,
                    end_time=end_time,
                    ordered_items=[],
                    food_total=0,
                    gst=0,
                    service_charge=0,
                    grand_total=0
                )
        else:
            return render_template("confirmation.html", error="No available tables selected.")

    tables = df.to_dict(orient="records")
    return render_template("reserve.html", tables=tables)


@app.route("/menu", methods=["GET", "POST"])
def menu():
    df = pd.read_excel(FOODMENU_FILE)

    # Normalize column headers just in case
    df.columns = [col.strip() for col in df.columns]

    reservation = session.get('reservation')

    if not reservation:
        return redirect("/reserve")

    if request.method == "POST":
        selected_items = request.form.getlist("selected_foods")
        ordered = []

        for item in selected_items:
            qty_str = request.form.get(f"quantity_{item}")
            if qty_str and qty_str.isdigit():
                quantity = int(qty_str)
                if quantity > 0:
                    food_row = df[df["Food Item"] == item].iloc[0]
                    price = food_row["Price:"] if "Price:" in food_row else food_row["Price"]
                    subtotal = price * quantity
                    gst = round(subtotal * 0.18, 2)
                    service_charge = round(subtotal * 0.05, 2)
                    total = round(subtotal + gst + service_charge, 2)

                    ordered.append({
                        "name": item,
                        "price": price,
                        "quantity": quantity,
                        "subtotal": subtotal,
                        "gst": gst,
                        "service_charge": service_charge,
                        "total": total
                    })

        if not ordered:
            error = "Please select at least one item with quantity > 0."
            return render_template("menu.html", food_items=df.to_dict(orient="records"), error=error)

        food_total = round(sum(item["subtotal"] for item in ordered), 2)
        gst = round(sum(item["gst"] for item in ordered), 2)
        service_charge = round(sum(item["service_charge"] for item in ordered), 2)
        grand_total = round(sum(item["total"] for item in ordered), 2)

        # Save confirmation to Excel
        confirmation_data = []

        for item in ordered:
            confirmation_data.append({
                "Name": reservation["name"],
                "Mobile": reservation["mobile"],
                "Reserved Tables": ", ".join(str(t) for t in reservation["tables"]),
                "Start Time": reservation["start_time"],
                "End Time": reservation["end_time"],
                "Food Item": item["name"],
                "Quantity": item["quantity"],
                "Price": item["price"],
                "Subtotal": item["subtotal"],
                "GST": item["gst"],
                "Service Charge": item["service_charge"],
                "Item Total": item["total"],
                "Order Total": grand_total
            })

        confirmation_df = pd.DataFrame(confirmation_data)
        # if os.path.exists(FINAL_CONFIRMATION_FILE):
        #     existing_df = pd.read_excel(FINAL_CONFIRMATION_FILE)
        #     updated_df = pd.concat([existing_df, confirmation_df], ignore_index=True)
        # else:
        #     updated_df = confirmation_df
        # updated_df.to_excel(ORIGINAL_FINAL_CONFIRMATION_FILE, index=False)

        if not os.path.exists(FINAL_CONFIRMATION_FILE):
            if os.path.exists(ORIGINAL_FINAL_CONFIRMATION_FILE):
                shutil.copy(ORIGINAL_FINAL_CONFIRMATION_FILE, FINAL_CONFIRMATION_FILE)
            else:
                pd.DataFrame(columns=['Name',	'Mobile,'	'Reserved Tables',	'Start Time',	'End Time',	'Food Item',	'Quantity',	'Price',	'Subtotal',	'GST',	'Service Charge',	'Item Total',	'Order Total'
]).to_excel(FINAL_CONFIRMATION_FILE, index=False)
        
        existing_df = pd.read_excel(FINAL_CONFIRMATION_FILE)
        updated_df = pd.concat([existing_df, confirmation_df], ignore_index=True)
        updated_df.to_excel(FINAL_CONFIRMATION_FILE, index=False)

        return render_template("confirmation.html",
            name=reservation["name"],
            mobile=reservation["mobile"],
            tables=reservation["tables"],
            start_time=reservation["start_time"],
            end_time=reservation["end_time"],
            ordered_items=ordered,
            food_total=food_total,
            gst=gst,
            service_charge=service_charge,
            grand_total=grand_total
        )

    return render_template("menu.html", food_items=df.to_dict(orient="records"))

#cancellation

@app.route("/cancel_reservation/<int:reservation_index>", methods=["POST"])
def cancel_reservation(reservation_index):
    if not os.path.exists(RESERVATIONS_FILE):
        return redirect("/myreservations")

    reservations = pd.read_excel(RESERVATIONS_FILE)

    if reservation_index in reservations.index:
        table_id = reservations.loc[reservation_index, "Table ID"]
        reservations = reservations.drop(index=reservation_index)

        # Mark table as Available
        tables_df = pd.read_excel(TABLE_FILE)
        tables_df.loc[tables_df["Table ID"] == table_id, "Availability"] = "Available"
        tables_df.to_excel(TABLE_FILE, index=False)

        reservations.to_excel(RESERVATIONS_FILE, index=False)

    return redirect("/myreservations")

@app.route("/myreservations")
def my_reservations():
    username = session.get("username")
    if not username:
        return redirect("/login")

    if not os.path.exists(RESERVATIONS_FILE):
        return render_template("myreservations.html", reservations=[], message="No active reservations found.")

    reservations = pd.read_excel(RESERVATIONS_FILE)

    if "Username" not in reservations.columns:
        return render_template("myreservations.html", reservations=[], message="Reservation data is missing user info.")

    # Filter reservations for this user only
    user_reservations = reservations[reservations["Username"] == username]

    if user_reservations.empty:
        return render_template("myreservations.html", reservations=[], message="No active reservations found.")

    user_reservations = user_reservations.reset_index()  # Optional for row access
    return render_template("myreservations.html", reservations=user_reservations.to_dict(orient="records"))

# ✅ New route just for returning from confirmation
@app.route("/back_to_dashboard")
def back_to_dashboard():
    username = session.get("username", "Guest")
    if username == "Guest":
        return redirect("/login")

    can_order = 'reservation' in session and session['reservation']
    return render_template("dashboard.html", username=username, can_order=can_order)

###logout

@app.route("/logout")
def logout():
    session.pop("username", None)
    return redirect("/login")

#####forgot pswd

import pandas as pd
import os
import smtplib
from flask import Flask, request, redirect, render_template, url_for, session
from email.mime.text import MIMEText
from itsdangerous import URLSafeTimedSerializer

@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    message = ""
    if request.method == "POST":
        email = request.form["email"]
        df = pd.read_excel(USER_FILE)

        if email in df["email"].values:
            token = s.dumps(email, salt="email-reset")
            reset_link = url_for('reset_password', token=token, _external=True)

            # Send Email
            sender = "maaranparottakadai2@gmail.com"
            password = "epbv xslb jtzv ncmf"  # Use your App Password here
            receiver = email

            msg = MIMEText(f"Click to reset your password: {reset_link}")
            msg["Subject"] = "Reset Your Password"
            msg["From"] = sender
            msg["To"] = receiver

            try:
                server = smtplib.SMTP("smtp.gmail.com", 587)
                server.starttls()
                server.login(sender, password)
                server.sendmail(sender, receiver, msg.as_string())
                server.quit()
                message = "Reset link sent to your email."
            except Exception as e:
                message = f"Error sending email: {e}"
        else:
            message = "Email not found."

    return render_template("forgot_password.html", message=message)

@app.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    try:
        email = s.loads(token, salt="email-reset", max_age=1800)  # Valid for 30 minutes
    except Exception:
        return "<p style='color:red;'>Invalid or expired reset link.</p>"

    message = ""
    if request.method == "POST":
        new_password = request.form["new_password"]
        df = pd.read_excel(USER_FILE)
        df.loc[df["email"] == email, "password"] = new_password
        df.to_excel(USER_FILE, index=False)
        return redirect("/login")

    return render_template("reset_password.html", message=message)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)

