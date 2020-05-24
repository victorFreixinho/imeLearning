from flask import Flask, request, session, send_file, redirect, send_from_directory
from twilio.twiml.messaging_response import MessagingResponse
import mysql.connector
import random
import pdfkit
# table de user chama-se user_info
# Por enqnt são 10 questões e só existe teste de matemática
# telefone guardado por +55XXXXXXXX (testar com romero se dá problema)
db = mysql.connector.connect(
    host='database-chatbot.ctcyc2sm3y3o.us-west-2.rds.amazonaws.com',
    user='pedro',
    password='SENHA_DB',
    auth_plugin='mysql_native_password',
    database='chatbotuser',
    port=3306
)
cursor = db.cursor()
application = Flask(__name__, static_url_path='', static_folder='static')
application.secret_key = 'secretpassword'


@application.route("/")
def root():
    return application.send_static_file("out.pdf")


@application.route('/bot', methods=['POST'])
def bot():
    print(request.values)
    from_tel = request.values.get('From', '').replace("whatsapp:", "")
    to_tel = request.values.get('To', '').replace('whatsapp:', "")
    if from_tel == '+14155238886':
        chatbot_tel = from_tel
        user_tel = to_tel
    else:
        chatbot_tel = to_tel
        user_tel = from_tel
    print("Numero do user:" + user_tel)
    print("Esse é o numero do bot: " + chatbot_tel)
    query = "SELECT nome FROM user_info WHERE telefone = %s"
    cursor.execute(query, (user_tel,))
    query_results = cursor.fetchall()
    if cursor.rowcount != 0:
        for nome in query_results:
            full_name = nome
            first_name = str(full_name).split()[0]
            session['nome'] = first_name
            session['user'] = 1
    incoming_msg = request.values.get('Body', '')
    if incoming_msg == 'RESET':
        session.clear()
        responded = True
    else:
        responded = False
    resp = MessagingResponse()
    msg = resp.message()
    try:
        if session['user'] == 1:
            responded = True
            if session['path'] == 'receive':
                if session['purpose'] == 'name':
                    # REGISTRO NOME
                    full_name = incoming_msg
                    msg.body("Obrigado por escolher contar com nossa ajuda," + full_name + '''.
Nosso objetivo é conseguir te diagnosticar nas matérias para fornecer o material adequado à você! 
Essas são as opções de testes até então:
Digite 1 se você quer um teste de matemática!(*por favor, digite somente o número*)''')
                    query_name = "INSERT INTO user_info(telefone, nome) values(%s,%s)"
                    values_name = [user_tel, full_name]
                    cursor.execute(query_name, values_name)
                    db.commit()
                    session['path'] = 1
                    session['purpose'] = 'Nada'
                elif session['purpose'] == 'answers':
                    # ENVIO QUESTÕES
                    respostas = incoming_msg
                    respostas = respostas.upper()
                    # Aqui vem análise de respostas
                    # Calculos doidos
                    msg.body('''Em algum momento teremos uma nota pra você, e uma lista de assuntos em ordem crescente de % de acerto
1 - Geometria - %
2 - Algebra Básica - %
3 - Mat. Financeria - %
4 - Alglin - %
5 - Grupos e Aneís - %
Sua proficiência em Matemática vale:
Digite o número que deseja focar essa semana.''')
                    session['path'] = 2
                    session['purpose'] = 'Nada'
            elif session['path'] == 1:
                if incoming_msg == '1':
                    # TESTE MATEMÁTICA
                    query_simulado_faceis = "SELECT nome_drive FROM math_questions WHERE dificuldade<5"
                    query_simulado_medias = "SELECT nome_drive FROM math_questions WHERE dificuldade<5"
                    query_simulado_dificeis = "SELECT nome_drive FROM math_questions WHERE dificuldade<5"
                    escolha_facil = random.sample(range(1, len(query_simulado_faceis)), 5)
                    nome_faceis = []
                    escolha_media = random.sample(range(1, len(query_simulado_medias)), 3)
                    nome_medias = []
                    escolha_dificil = random.sample(range(1, len(query_simulado_dificeis)), 2)
                    nome_dificeis = []
                    cursor.execute(query_simulado_faceis)
                    questoes_simu = cursor.fetchall()
                    print(cursor.rowcount)
                    i = 1
                    for nome_drive in questoes_simu:
                        if i in escolha_facil:
                            nome_faceis.append(nome_drive)
                        i = i + 1
                    cursor.execute(query_simulado_medias)
                    questoes_simu = cursor.fetchall()
                    i = 1
                    for nome_drive in questoes_simu:
                        if i in escolha_media:
                            nome_medias.append(nome_drive)
                        i = i + 1
                    cursor.execute(query_simulado_dificeis)
                    questoes_simu = cursor.fetchall()
                    i = 1
                    for nome_drive in questoes_simu:
                        if i in escolha_dificil:
                            nome_dificeis.append(nome_drive)
                        i = i + 1
                    # AQUI ENTRA XANDE CRIANDO HTML
                    # retornou um arquivo html no meu diretorio.
                    file_path = 'file.html'
                    pdfkit.from_file(input='/home/pedro/PycharmProjects/hackathon/file.html',
                                     output_path='static/out.pdf')
                    msg.media('/')
                    session['path'] = 'receive'
                    session['purpose'] = 'answers'
                    # FINAL ENVIO SIMULADO
            elif session['path'] == 2:
                if incoming_msg is not None:
                    msg.body('''Aqui terá uma recomendação massa de vídeos
Após estudo do material, venha novamente testar seus conhecimentos!''')
                    session.clear()
    except KeyError:
        if not responded:
            msg.body('''Seja bem-vindo ao seu ajudante virtual de estudo!
Nosso objetivo é criar uma curadoria personalizada com base no seu conhecimento em cada matéria, facilitando
seu estudo à distância de forma inteligente, buscando sempre auxiliar na construção gradativa de conteúdo para que você não se sinta nem pouco desafiado nem desestimulado!
Fazemos isso com um teste diagnóstico de 10 questões de uma matérias específica. Com base nos seus acertos, vamos começar a predizer seu nível de conhecimento por meio da TRI!
Sim, o mesmo método usado pelo *ENEM*. Dessa forma conseguirmos medir sua proficiência em certa matéria, garantindo que você tenha conteúdo de acordo com seu nível!
Percebemos que você *não possui cadastro conosco*, por favor, nos diga na sua próxima mensagem qual seu nome.''')
            session['user'] = 1
            session['path'] = 'receive'
            session['purpose'] = 'name'
        else:
            msg.body('''Tivemos um problema em nossa base de dados, contudo, ainda temos seu cadastro!

Essas são as opções de testes até então:
Digite 1 se você quer um teste de matemática!(*por favor, digite somente o número*)''')
            session['user'] = 1
            session['path'] = 1
    return str(resp)


if __name__ == '__main__':
    application.run()
