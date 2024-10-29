from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Database connection
conn = mysql.connector.connect(
    host='sql12.freesqldatabase.com',
    user='sql12741246',
    password='2XqTdR7LCV',
    database='sql12741246',
    port=3306
)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE UserName = %s", (username,))
        user = cursor.fetchone()
        
        if user:
            session['user'] = user['UserName']
            return redirect(url_for('agreements'))
        else:
            return "Invalid credentials", 401
    return render_template('login.html')

@app.route('/agreements')
def agreements():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PA_Header")
    agreements = cursor.fetchall()
    
    return render_template('agreements.html', agreements=agreements)

@app.route('/agreement/<int:agreement_id>', methods=['GET', 'POST'])
def agreement_details(agreement_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        new_costs = request.form.getlist('new_costs')
        sku_numbers = request.form.getlist('sku_numbers')
        
        for i in range(len(sku_numbers)):
            new_cost = new_costs[i].strip()
            
            if new_cost:
                sku_number = sku_numbers[i]
                cursor.execute("UPDATE PA_Detail SET New_Cost = %s WHERE Agreement_No = %s AND SKU_Number = %s", 
                               (new_cost, agreement_id, sku_number))

                cursor.execute("INSERT INTO PA_Audit (Agreement_No, SKU_Number, Old_Cost, New_Cost, UpdatedBy) "
                               "SELECT Agreement_No, SKU_Number, Cost, %s, %s FROM PA_Detail WHERE Agreement_No = %s AND SKU_Number = %s",
                               (new_cost, session['user'], agreement_id, sku_number))

        conn.commit()
        return redirect(url_for('agreements'))

    cursor.execute("SELECT * FROM PA_Detail WHERE Agreement_No = %s", (agreement_id,))
    records = cursor.fetchall()
    
    return render_template('agreement_details.html', records=records, agreement_id=agreement_id)

@app.route('/audit')
def audit():
    if 'user' not in session:
        return redirect(url_for('login'))

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PA_Audit")
    audits = cursor.fetchall()
    
    return render_template('audit.html', audits=audits)

@app.route('/audit/delete/<int:audit_id>', methods=['POST'])
def delete_audit(audit_id):
    cursor = conn.cursor()
    cursor.execute("DELETE FROM PA_Audit WHERE Audit_ID = %s", (audit_id,))
    conn.commit()
    return redirect(url_for('audit'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# if __name__ == '__main__':
#     app.run(debug=True)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
