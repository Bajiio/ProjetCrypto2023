import os, random, time, re, smtplib, secrets, subprocess, glob, csv
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders



def upload_csr(csrFile, email):
    print("email = " + email)
    directoryPath = '../CA/csr'
    fileName = time.strftime("%Y_%m_%d-%H_%M_%S", time.localtime()) + '.csr'
    os.makedirs(directoryPath, exist_ok=True)
    csrFile.save(os.path.join(directoryPath, fileName))
    return os.path.join(directoryPath, fileName)


def is_valid_email(email):
    regex = r'^[\w-]+(?:\.[\w-]+)*@(?:[\w-]+\.)+[a-zA-Z]{2,7}$'
    return re.match(regex, email)

def sendEmail(recipient_email,mode):
    # Adresse e-mail de l'expéditeur et mot de passe SMTP
    sender_email = "projetcrypto2023@gmail.com"
    password = "bhoxgybwypaeldjx"

    # Vérification de l'adresse e-mail
    if not is_valid_email(recipient_email):
        print("Adresse e-mail invalide.")
    else:
        # Création du message de vérification
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = recipient_email
        if mode == 0:
            msg['Subject'] = "Vérification de l'adresse e-mail"
            code = random.randrange(100000,999999) # Code de vérification aléatoire à générer
            body = "Votre code de vérification est : " + str(code)
        else:
            revokeCode= random.randrange(100000,999999)
            msg['Subject'] = "Votre Nouveau Certificat pour signer vos mails !"
            body = "Vous trouverez en pièce jointe votre certificat.\n\nPour l'utiliser avec Thunderbird, convertisser le en pk12 avant de l'importer. (ex : 'openssl pkcs12 -export -out toImport.p12 -in moncert.pem -inkey myprivatekey')\n\nVoici votre code pour révoquer votre certificat, veuillez le conserver précieusement:"+ str(revokeCode) # file upload here
        msg.attach(MIMEText(body, 'plain'))
        if mode !=0:
            filename = mode
            with open(filename, 'rb') as f:
                attachment = MIMEBase('application', 'octet-stream')
                attachment.set_payload(f.read())
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', 'attachment', filename=filename.split('/')[-1])
                msg.attach(attachment)

        with smtplib.SMTP('smtp.gmail.com', 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(sender_email, password)
            smtp.send_message(msg)
            smtp.quit()
    if mode ==0:
        return code
    else:
        registerCode(recipient_email,revokeCode)
        return "FILE SUCCESSFULLY SENT"
    


def checkCode(code,verifCode):

    # Vérification du code de vérification
    if code == verifCode:
        print("Adresse e-mail vérifiée avec succès.")
        return secrets.token_urlsafe(16)
    else:
        print("Code de vérification invalide.")
        return 0
    
def genCert(email, csrFile):
    exist=findCert(email)
    print("exist =" + exist)
    if exist != "ERROR":
        return "EXISTING"
    else:
        result = subprocess.run(['./verifAndGenCert.sh', csrFile, email ], stdout=subprocess.PIPE).stdout.decode('utf-8')
        if result == "1":
            return "Certificat bien généré"
        else:
            return "Erreur lors de la génération du certificat ou de la vérification du mail de la requête"
    
def findCert(email):
    path='../CA/newcerts/*'
    files = list(filter(os.path.isfile, glob.glob(path)))
    files.sort(key=lambda x: os.path.getmtime(x))
    print(files)
    i=0
    if files != []:
        lastFile=files[-1]
        result = subprocess.run(['./verifyMail.sh', lastFile, email ], stdout=subprocess.PIPE).stdout.decode('utf-8')
        while(result != "1" and i<len(files)):
            lastFile=files[i]
            i=i+1
            result = subprocess.run(['./verifyMail.sh', lastFile, email ], stdout=subprocess.PIPE).stdout.decode('utf-8')
        if i==len(files):
            return "ERROR"
        return lastFile
    else:
        return "ERROR3"

def sendCert(email):
    cert=findCert(email)
    print("cert=",cert)
    if cert == "ERROR":
        return "ERROR finding cert in server"
    else:
        sendEmail(email,cert)
        return "Certificat envoyé à l'adresse mail : " + email


def registerCode(email,code):
# Define the file name and column names
    filename = 'revoke_code.csv'

    # Open the file in write mode and create the csv.writer object
    with open(filename, 'a', newline='') as csvfile:
        writer = csv.writer(csvfile)

        # Write the username and code data for each user
        writer.writerow([email, code])

        # Close the file
        csvfile.close()


def checkRevoke(email,code):
    filename = 'revoke_code.csv'
    code=str(code)
    print("code & email:",code,email)

    # Open the file in read mode and create the csv.reader object
    with open(filename, 'r') as csvfile:
        reader = csv.reader(csvfile)

        # Iterate over the rows in the file
        for row in reader:
            print(row)
            # Check if the current row matches the username and code combination
            if row[0] == email and row[1] == code:
                print('User found!')
                csvfile.close()
                deleteLine(email)
                result=revokeCert(email)
                if result == "ERROR NO CERT FOUND":
                    return -2
                return 1
        else:
            print('User not found')
            csvfile.close()
            return -1

def deleteLine(email):
    filename = 'revoke_code.csv'
        # Open the file in read mode and read its contents into a list
    with open(filename, 'r') as f:
        lines = f.readlines()

    # Loop through the list and find the line you want to delete
    for i, line in enumerate(lines):
        if line.startswith(f"{email}"):
            # Once you find the line, use the pop() method to remove it from the list
            lines.pop(i)
            break

    # Close the file
    f.close()

    # Reopen the file in write mode and write the modified list back to the file
    with open(filename, 'w') as f:
        f.writelines(lines)
        
    # Close the file
    f.close()

def revokeCert(email):
    cert=findCert(email)
    if cert=="ERROR":
        return "ERROR NO CERT FOUND"
    result = subprocess.run(['./revokeCert.sh', cert], stdout=subprocess.PIPE).stdout.decode('utf-8')
    print("REVOKED")
    return result