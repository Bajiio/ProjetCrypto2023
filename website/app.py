from http.client import HTTPException
from flask import Flask, render_template, request, redirect, Response, url_for, flash, session, abort
from functionCert import *
import base64
from Crypto.Cipher import AES


app = Flask(__name__)
app.config['SECRET_KEY'] = '46421764e6bb1cd09c1cb6d3b25d3fcee41784f77da6b6a0'
app.secret_key='c286022b78d255175de34218c0350d89b9c54191ee210d53'


@app.route('/csrRequest/<token>/<success>', methods=['GET']) #Page pour soumettre son fichier csr
def display_form(token,success=None):
    try:
        if token == decrypt_data(session.get('token')):
            return render_template('form.html',success=success,email=decrypt_data(session['email']))    
        return redirect(url_for('connectEmail'))
    except IndexError:
        abort(404)
    except HTTPException:
        abort(404)

@app.route('/upload', methods=['POST']) # Page ou la requete post du formulaire csr est envoyé
def upload():
    if request.method == 'POST':
        csrFile = request.files['csr']
        email = decrypt_data(session.get('email'))
        if not csrFile or not '.' in csrFile.filename or not csrFile.filename.rsplit('.', 1)[1].lower() == 'csr' :
            flash('correct CSR is required!')
        elif not is_valid_email(email):
            flash('Email is required!')
        else:
            path=upload_csr(csrFile, email)
            flash('Form submitted successfully!')
            messageGen = genCert(email, path)
            print("messageGen = " + messageGen)
            if messageGen == "EXISTING":
                flash('Certificat already generated for this email!')
            else:
                flash(messageGen)
            messageSend = sendCert(email)
            flash(messageSend)
            return redirect(url_for('display_form', token=decrypt_data(session.get('token')),success=True))
    return redirect(url_for('display_form',token = request.args.get('token'),success=False))

@app.route('/check', methods=['GET','POST'])# Page pour check l'otp
def check():
    try:
        if request.method == 'POST':
            print(request.form.get('revoke'))
            if request.form.get('revoke')=='False':
                code = request.form['code']
                email = request.form.get('email')
                token = checkCode(code,decrypt_data(session.get('code')))
                print('token',str(token))
                if token != 0:
                    flash('Email is verified!')
                    session['token'] = encrypt_data(token)
                    session['email'] = encrypt_data(email)
                    return redirect(url_for('display_form',token=token,success=True))
                else:
                    flash('Code is not correct!')
                    print('redirect and token =' + str(token)+ ' / email = ' + email)
                    return redirect(url_for('check', email =email, success = False,revoke=False))
            else:
                code = request.form['code']
                email = decrypt_data(session.get('email'))
                if email != None:
                        check=checkRevoke(email,code)
                        if check == 1:
                            #Revoke Cert here
                            flash('Your certificate has been revocated')
                            return redirect(url_for('display_form',token=decrypt_data(session.get('token')),success=True))
                        
                        elif check ==-2:
                            flash('Certificat non trouvé')
                            return redirect(url_for('check',email=email,success=False,revoke=request.form.get('revoke')))
                        else:
                            flash('Faux code de révocation')
                            return redirect(url_for('check',email=email,success=False,revoke=request.form.get('revoke')))       
                else:
                    flash('Email non connecté')
                    return redirect(url_for('connectEmail',success=False))
        return render_template('checkCode.html',email=request.args.get('email'),success=request.args.get("success"),revoke=request.args.get('revoke'))
    except IndexError:
        abort(404)
    except HTTPException:
        abort(404)

@app.route('/connectEmail/<success>', methods=['GET','POST'])
@app.route('/', methods=['GET','POST'])  # Page pour verifier son email
def connectEmail(success=None):
    try:
        if request.method == 'POST':
            email = request.form['email']
            if not is_valid_email(email):
                flash('Email is required!')
                return redirect(url_for('connectEmail',success=False))
            else:
                session['code']  = encrypt_data(str(sendEmail(email,0)))
                flash('Email is sent!')
                return redirect(url_for('check',email=email,success=True,revoke=False))
        return render_template('connectEmail.html',success=success)
    except IndexError:
        abort(404)
    except HTTPException:
        abort(404)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

# Fonction pour chiffrer les données avec AES
def encrypt_data(data):
    key = app.secret_key[:16]
    cipher = AES.new(key, AES.MODE_ECB)
    padded_data = data + (AES.block_size - len(data) % AES.block_size) * chr(AES.block_size - len(data) % AES.block_size)
    encrypted_data = cipher.encrypt(padded_data.encode())
    return base64.b64encode(encrypted_data).decode()

# Fonction pour déchiffrer les données avec AES
def decrypt_data(encrypted_data):
    key = app.secret_key[:16]
    cipher = AES.new(key, AES.MODE_ECB)
    decrypted_data = cipher.decrypt(base64.b64decode(encrypted_data)).decode()
    return decrypted_data.rstrip(chr(ord(decrypted_data[-1])))

if __name__ == '__main__':
    from waitress import serve
    serve(app, host='127.0.0.1', port=5000, threads=1)