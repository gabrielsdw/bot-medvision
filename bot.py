import telebot
import requests
import pymongo as pg
import datetime
import pytz


myclient = pg.MongoClient("mongodb+srv://gabrielsdw:Adriano74@cluster0.xywxkos.mongodb.net/")

mydb = myclient['dados_bot']
mycol = mydb["customers"]

BOT_TOKEN = '6510088960:AAFl7iSsgyTIhEqaBoFrG7n7LXQdh-urHhM'

url = 'https://medvision-bebb0add5e3e.herokuapp.com/classificationApp'
url_caption = 'https://medvision-bebb0add5e3e.herokuapp.com/classification-app-tag'

traducao_orgaos = {
    'Blood': 'Sangue',
    'Brain MRI': 'Cérebro MRI',
    'Chest CT': 'Pulmão CT',
    'Chest XR': 'Pulmão RAIO-X',
    'Knee MRI': 'Joelho MRI',
    'Knee XR': 'Joelho RAIO-X',
    'Liver MRI': 'Fígado MRI',
    'Eye': 'Olho',
    'Non medical image':'Imagem não médica'
}

classes_index = {
    'Blood': [0, 'Blood'],
    'Brain MRI': [1, 'Brain MRI'],
    'Chest CT': [2, 'Chest CT'],
    'Chest XR': [3, 'Chest XR'],
    'Knee MRI': [4, 'Knee MRI'],
    'Knee XR': [5, 'Knee XR'],
    'Liver MRI': [6, 'Liver MRI'],
    'Eye': [7, 'Eye']
}

captions = ['Brain MRI', 'Chest XR', 'Knee MRI', 'Knee XR', 'Liver MRI', 'Eye']

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['caption'])
def caption(message):
    user_id = message.chat.id
    
    msg1 = 'Em caso de erros do classificador geral você pode reenviar a imagem com uma legenda escrito o tipo correto da imagem.'
    msg2 = 'Legendas disponíveis \n\nBrain MRI\nChest XR\nKnee MRI\nKnee XR\nLiver MRI\nEye'
    bot.send_message(user_id, msg1)
    bot.send_message(user_id, msg2)


def post(url, file, existsCaption, caption):
    if not existsCaption:
        response = requests.post(url=url, files={'uploaded_file': file})
    else:
        file = {'uploaded_file': file}
        form = {'class_index': classes_index[caption][0], 'class_name': classes_index[caption][1]}

        response = requests.post(url=url_caption, files=file, data=form)

    if response.status_code != 200:
        print("API ERROR")
        return
    
    response = response.json()

    if 'doenca' in response.keys():
        return {
            'cond': True,
            'diagnostico': response['doenca'],
            'tipoImagem': response['tipoImagem']
        }
    else:
        return {
            'cond': False,
            'diagnostico': False,
            'tipoImagem': response['tipoImagem']
        }


@bot.message_handler(content_types=['photo'])
def classifierImage(message):
    existCaption = True if message.caption is not None else False

    try:
        file_id = message.photo[-1].file_id
            
        file_info = bot.get_file(file_id)
            
        file_path = file_info.file_path

        downloaded_file = bot.download_file(file_path)

        caption = message.caption

        if existCaption:
            if caption not in captions:
                caption = False
            info = post(url=url_caption, file=downloaded_file, existsCaption=existCaption, caption=caption)
        else:
            info = post(url=url, file=downloaded_file, existsCaption=existCaption, caption=str())

        cond, diagnostico, tipoImagem = info['cond'], info['diagnostico'], info['tipoImagem']

        tipoImagem = traducao_orgaos[tipoImagem]

        if cond:
            labels = organizarLabel(diagnostico=diagnostico)
            
            msg = 'Foi detectado uma imagem não médica ou que não é suportada pelo sistema.\n\nEnvie uma imagem válida.'
            msg = f"Tipo da Imagem: {tipoImagem}\n\nDiagnóstico: \n{labels}" if diagnostico else msg
        else:
            msg = f'Tipo da Imagem: {tipoImagem}\n\nInsira um tipo de imagem médica!\n\nPara dúvidas digite: /help'

        bot.reply_to(message, msg)

        user_data = returnUserData(message, tipoImagem)
        mycol.insert_one(user_data)
        
    except Exception as e:
        print(str(e))
        bot.reply_to(message, 'Foi detectado uma imagem não médica ou que não é suportada pelo sistema.\nEnvie uma imagem válida') 


def returnUserData(message, tipoImagem):
    timezone = pytz.timezone('Etc/GMT+3')
    current_time = datetime.datetime.now(timezone)
    data_atual = str(datetime.datetime.now())
    data, hora = data_atual.split()
    hora = hora.split(".")[0]

    user_data = {
        'user_id': message.from_user.id,
        'data': data,
        'hora': hora,
        'saida_cg': tipoImagem
    }
    return user_data


def organizarLabel(diagnostico):
    labels = ''
    for diagnostico, probabilidade in diagnostico.values():
        labels += f'{diagnostico}: {round(float(probabilidade))}%\n'
    return labels


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id

    msg1 = f"Olá, {message.from_user.first_name} seja bem-vindo ao MedVision!\n" 
    msg2 = "Para fazer diagnósticos basta enviar sua imagem.\n"
    msg3 = "Em caso de dúvidas digite: /help\n"
        
    bot.send_message(user_id, msg1)
    bot.send_message(user_id, msg2)
    bot.send_message(user_id, msg3)
    

@bot.message_handler(commands=['help'])
def help(message):
    user_id = message.chat.id

    comandos = 'Comandos\n' + \
               '/info - Mostra informações sobre o projeto\n'  + \
               '/team - Mostra meios de contato à equipe\n' + \
               '/types - Mostra os tipos de imagens suportadas\n' + \
               '/cg - Mostra informações sobre o classificador geral\n' + \
               '/caption - Ajusta erros do classificador geral'
    
    bot.send_message(user_id, comandos)


@bot.message_handler(commands=['cg'])
def cg(message):
    user_id = message.chat.id

    msg_title = 'Classificador Geral'
    msg = 'O classificador geral é usado antes de passar a imagem ao modelo para a classificação da enfermidade. Ele é o responsável por detectar o tipo de imagem (Raio-X do Pulmão, Oftalmoscopia...) e redirecionar a imagem para o respectivo modelo. Caso o usuário insira uma imagem que não condiza com algum dos modelos acima, o sistema retornará uma mensagem de erro.'

    bot.send_message(user_id, msg_title)
    bot.send_message(user_id, msg)


@bot.message_handler(commands=['C0NS8LT_B4'])
def consult_bd(message):
    user_id = message.chat.id

    qtdI = mycol.count_documents({})
    qtdP = len(mycol.distinct('user_id'))

    for x in mycol.find():
        id, data, hora, saida_cg = x['user_id'], x['data'], x['hora'], x['saida_cg']
        info = f'user_id: {id}, data: {data}, hora: {hora}, saida_cg: {saida_cg}'
        bot.send_message(user_id, info)

    bot.send_message(user_id, f'I: {qtdI} | P: {qtdP}')


@bot.message_handler(commands=['types'])
def types(message):
    user_id = message.chat.id

    msg = 'Tipos de Imagens Atualmente Suportadas'
    msg2 = 'Ressonância Magnética do Cérebro\n' + \
           'Ressonância Magnética do Joelho\n' + \
           'Ressonância Magnética do Fígado\n' + \
           'Raio-X do Pulmão\n' + \
           'Raio-X do Joelho\n' + \
           'Oftalmoscopia'

    bot.send_message(user_id, msg)
    bot.send_message(user_id, msg2)


@bot.message_handler(commands=['info'])
def info(message):
    user_id = message.chat.id

    title = "Sobre o Projeto MedVision"
    msg1_txt = "O MedVision é uma iniciativa desenvolvida por uma equipe de pesquisadores do Instituto Federal do Triângulo Mineiro (IFTM) Campus Ituiutaba. O projeto tem como objetivo, o uso de ferramentas de Deep Learning e Inteligência Artificial para o auxiliar o diagnóstico de enfermidades por meio de análises automatizadas de imagens médicas. Atualmente a aplicação conta com cinco modelos para análise de diferentes regiões do corpo, além de um modelo (Classificador Geral) com o próposito de redirecionar automaticamente à região do corpo recorrespondente de acordo com o tipo de imagem enviada pelo usuário."
    bot.send_message(user_id, title)
    bot.send_message(user_id, msg1_txt)
    

@bot.message_handler(commands=['team'])
def team(message):
    user_id = message.chat.id

    msg_title =  "Equipe"
    msg_txt = 'André Luiz França Batista\nLinktree: https://linktr.ee/andre.batista' + \
                '\n\n\nBruno Gomes Pereira\nLinktree: https://linktr.ee/brunaogomes' + \
                '\n\n\nGabriel Oliveira Santos\nLinktree: https://linktr.ee/gabrielsdw' + \
                '\n\n\nJoão Pedro Araujo\nLinktree: https://linktr.ee/joaopedroaqb' + \
                '\n\n\nMatheus Ricardo de Jesus\nLinktree: https://linktr.ee/mathi.tar'
    bot.send_message(user_id, msg_title)
    bot.send_message(user_id, msg_txt)


if __name__ == '__main__':
    bot.infinity_polling()
