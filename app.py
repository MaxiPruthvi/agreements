from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))  # Secret key from environment for security

# Database connection function
def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get('DB_HOST', 'sql12.freesqldatabase.com'),
        user=os.environ.get('DB_USER', 'sql12741246'),
        password=os.environ.get('DB_PASSWORD', '2XqTdR7LCV'),
        database=os.environ.get('DB_NAME', 'sql12741246'),
        port=int(os.environ.get('DB_PORT', 3306))
    )

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE UserName = %s", (username,))
        user = cursor.fetchone()
        conn.close()
        
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

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PA_Header")
    agreements = cursor.fetchall()
    conn.close()
    
    return render_template('agreements.html', agreements=agreements)

@app.route('/agreement/<int:agreement_id>', methods=['GET', 'POST'])
def agreement_details(agreement_id):
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        new_costs = request.form.getlist('new_costs')
        sku_numbers = request.form.getlist('sku_numbers')
        
        for i in range(len(sku_numbers)):
            new_cost = new_costs[i].strip()
            
            if new_cost:
                sku_number = sku_numbers[i]
                
                # Update both New_Cost and Cost columns
                cursor.execute("""
                    UPDATE PA_Detail 
                    SET New_Cost = %s, Cost = %s 
                    WHERE Agreement_No = %s AND SKU_Number = %s
                """, (new_cost, new_cost, agreement_id, sku_number))

                # Insert the audit entry
                cursor.execute("""
                    INSERT INTO PA_Audit (Agreement_No, SKU_Number, Old_Cost, New_Cost, UpdatedBy)
                    SELECT Agreement_No, SKU_Number, Cost, %s, %s 
                    FROM PA_Detail 
                    WHERE Agreement_No = %s AND SKU_Number = %s
                """, (new_cost, session['user'], agreement_id, sku_number))

        conn.commit()

    # Fetch the updated records for display
    cursor.execute("SELECT * FROM PA_Detail WHERE Agreement_No = %s", (agreement_id,))
    records = cursor.fetchall()
    conn.close()
    
    return render_template('agreement_details.html', records=records, agreement_id=agreement_id)

@app.route('/audit')
def audit():
    if 'user' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM PA_Audit")
    audits = cursor.fetchall()
    conn.close()
    
    return render_template('audit.html', audits=audits)

@app.route('/audit/delete/<int:audit_id>', methods=['POST'])
def delete_audit(audit_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM PA_Audit WHERE Audit_ID = %s", (audit_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('audit'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# Host and port for Render deployment
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
# Host and port for Render deployment
# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
if __name__ == '__main__':
    app.run(debug=True)