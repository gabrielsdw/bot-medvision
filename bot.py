import telebot
import requests

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

bot = telebot.TeleBot(BOT_TOKEN)

def salvarDados(message, file : str='dados.txt'):
    user_id = str(message.chat.id)
    
    with open(file, "a") as arquivo:
        arquivo.write(str(user_id)+'\n')


def post(url, file, existsCaption, caption):
    print(caption)
   
    if not existsCaption:
        response = requests.post(url=url, files={'uploaded_file': file})
    else:
        print(classes_index[caption][0], classes_index[caption][1])
        a = {'uploaded_file': file, 'class_index': str(classes_index[caption][0]), 'class_name': str(classes_index[caption][1])}
        response = requests.post(url=url_caption, files=a)
    print(response.status_code)
    if response.status_code == 200:
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
                'diagnostico': None,
                'tipoImagem': response['tipoImagem']
            }
    else:
        print("API ERROR")    


@bot.message_handler(content_types=['photo'])
def classifierImage(message):
    user_id = message.from_user.id

    existCaption = True if message.caption is not None else False

    try:
        file_id = message.photo[-1].file_id
            
        file_info = bot.get_file(file_id)
            
        file_path = file_info.file_path

        downloaded_file = bot.download_file(file_path)
        print(downloaded_file)
        caption = message.caption
        if existCaption:
            print("existe caption")
            info = post(url=url_caption, file=downloaded_file, existsCaption=existCaption, caption=caption)
            print(info)
        else:
            print('não existe caption')
            info = post(url=url, file=downloaded_file, existsCaption=existCaption, caption=str())
            print(info)
        print(info)
        cond, diagnostico, tipoImagem = info['cond'], info['diagnostico'], info['tipoImagem']

        tipoImagem = traducao_orgaos[tipoImagem]

        if cond:
            labels = organizarLabel(diagnostico=diagnostico) if diagnostico else " "
            print(labels)
            msg = f"Tipo da Imagem: {tipoImagem}\n\nDiagnóstico: \n{labels}"
        else:
            msg = f'Tipo da Imagem: {tipoImagem}\n\nInsira um tipo de imagem médica!\n\nPara dúvidas digite: /help'
            
        bot.reply_to(message, msg)
    except Exception as e:
        bot.reply_to(message, f"Erro ao processar a imagem: {str(e)}")


def organizarLabel(diagnostico):
    labels = ''
    for diagnostico, probabilidade in diagnostico.values():
        labels += f'{diagnostico}: {round(float(probabilidade))}%\n'
    return labels


@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    salvarDados(message=message, file='dados.txt')

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
               '/cg - Mostra informações sobre o classificador geral'
    bot.send_message(user_id, comandos)


@bot.message_handler(commands=['cg'])
def cg(message):
    user_id = message.chat.id

    msg_title = 'Classificador Geral'
    msg = 'O classificador geral é usado antes de passar a imagem ao modelo para a classificação da enfermidade. Ele é o responsável por detectar o tipo de imagem (Raio-X do Pulmão, Oftalmoscopia...) e redirecionar a imagem para o respectivo modelo. Caso o usuário insira uma imagem que não condiza com algum dos modelos acima, o sistema retornará uma mensagem de erro.'

    bot.send_message(user_id, msg_title)
    bot.send_message(user_id, msg)


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
                '\n\n\n João Pedro Araujo\nLinktree: https://linktr.ee/joaopedroaqb' + \
                '\n\n\n Matheus Ricardo de Jesus\nLinktree: https://linktr.ee/mathi.tar'
    bot.send_message(user_id, msg_title)
    bot.send_message(user_id, msg_txt)


if __name__ == '__main__':
    bot.infinity_polling()
