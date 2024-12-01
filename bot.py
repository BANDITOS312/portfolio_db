# импортируем все нужное
from logic import DB_Manager
from config import *
from telebot import TeleBot
from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telebot import types

# делаем бота
bot = TeleBot(TOKEN)
hideBoard = types.ReplyKeyboardRemove() 

# кнопка отмены
cancel_button = "Отмена 🚫"

# Команда закрытия
def cansel(message):
    bot.send_message(message.chat.id, "Чтобы посмотреть команды, используй - /info", reply_markup=hideBoard)

# команда на отсутствие проектов
def no_projects(message):
    # ввывод сообщения
    bot.send_message(message.chat.id, 'У тебя пока нет проектов!\nМожешь добавить их с помошью команды /new_project')

# генератор
def gen_inline_markup(rows):
    markup = InlineKeyboardMarkup()
    markup.row_width = 1
    for row in rows:
        markup.add(InlineKeyboardButton(row, callback_data=row))
    return markup

def gen_markup(rows):
    markup = ReplyKeyboardMarkup(one_time_keyboard=True)
    markup.row_width = 1
    for row in rows:
        markup.add(KeyboardButton(row))
    markup.add(KeyboardButton(cancel_button))
    return markup

# атрибуты для нового проекта
attributes_of_projects = {'Имя проекта' : ["Введите новое имя проекта", "project_name"],
                          "Описание" : ["Введите новое описание проекта", "description"],
                          "Ссылка" : ["Введите новую ссылку на проект", "url"],
                          "Статус" : ["Выберите новый статус задачи", "status_id"]}

# информация о проекте
def info_project(message, user_id, project_name):
    # берем инфу о проектах юзера
    info = manager.get_project_info(user_id, project_name)[0]
    # берем скилы проектов
    skills = manager.get_project_skills(project_name)
    # есил нет скилов то
    if not skills:
        # сообщение что нет скилов
        skills = 'Навыки пока не добавлены'
    # ввывод инфы о проекте
    bot.send_message(message.chat.id, f"""Project name: {info[0]}
Description: {info[1]}
Link: {info[2]}
Status: {info[3]}
Skills: {skills}
""")

# команда старт
@bot.message_handler(commands=['start'])
# сама функция старта
def start_command(message):
    # приветствие и рассказ что за бот
    bot.send_message(message.chat.id, """Привет! Я бот-менеджер проектов
Помогу тебе сохранить твои проекты и информацию о них!) 
""")
    # запуск функции info
    info(message)

# команда info
@bot.message_handler(commands=['info'])
# функция Info
def info(message):
    # ввывод списка команд
    bot.send_message(message.chat.id,
"""
Вот команды которые могут тебе помочь:

/new_project - используй для добавления нового проекта
/skills - добовляет скилл к выбраному проекту
/projects - выводит все ваши проекты
/update_projects - обновляет ваш проект
/delete - удаляет выбранный проект

Также ты можешь ввести имя проекта и узнать информацию о нем!""")
    

# команда добовления проекта
@bot.message_handler(commands=['new_project'])
def addtask_command(message):
    # вывод сообщения 
    bot.send_message(message.chat.id, "Введите название проекта:")
    # запускаем следующий хендлер name_project
    bot.register_next_step_handler(message, name_project)

# функция
def name_project(message):
    # имя проекта
    name = message.text
    # айди юзера
    user_id = message.from_user.id
    # список
    data = [user_id, name]
    # ввывод сообщения
    bot.send_message(message.chat.id, "Введите ссылку на проект")
    # некст хендлер
    bot.register_next_step_handler(message, link_project, data=data)

# функция
def link_project(message, data):
    # добовляем в data ссылку на проект
    data.append(message.text)
    # берем все статусы
    statuses = [x[0] for x in manager.get_statuses()] 
    # вывыдим статусы в виде панели для выбора
    bot.send_message(message.chat.id, "Введите текущий статус проекта", reply_markup=gen_markup(statuses))
    # запускаем следующий хендлер callback_project
    bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)

# Последняя функция для создания нового проекта
def callback_project(message, data, statuses):
    # берем статус
    status = message.text
    # есили text = кнопке отмены
    if message.text == cancel_button:
        # функция закрытия
        cansel(message)
        return
    # если такого статуса нет тогда
    if status not in statuses:
        # вывод сообщения об ошибке
        bot.send_message(message.chat.id, "Ты выбрал статус не из списка, попробуй еще раз!)", reply_markup=gen_markup(statuses))
        bot.register_next_step_handler(message, callback_project, data=data, statuses=statuses)
        return
    # берем id статуса
    status_id = manager.get_status_id(status)
    #добовляем id в data
    data.append(status_id)
    # добовляес в базу
    manager.insert_project([tuple(data)])
    # ввывод сообщения об удачном выполнение команд
    bot.send_message(message.chat.id, "Проект сохранен")


# команда для добовления скилов
@bot.message_handler(commands=['skills'])
def skill_handler(message):
    # берем id пользователя
    user_id = message.from_user.id
    # берем проекты пользователя 
    projects = manager.get_projects(user_id)
    # если есть проекты
    if projects:
        # берем все проекты
        projects = [x[2] for x in projects]
        # вывод сообщения и панель для выбора проекта
        bot.send_message(message.chat.id, 'Выбери проект для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    else:
        # если нет проектов, то пишем об этом пользователю
        no_projects(message)

# добовляем скил к проекту 
def skill_project(message, projects):
    # берм в переменную сообщение пользователя
    project_name = message.text
    # если это закрытие
    if message.text == cancel_button:
        # тогда запускаем функцию закрытия
        cansel(message)
        return
    
    #если такого проекта нет
    if project_name not in projects:
        # ввывод сообщения
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй еще раз!) Выбери проект для которого нужно выбрать навык', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, skill_project, projects=projects)
    
    #если есть
    else:
        # берем все навыки
        skills = [x[1] for x in manager.get_skills()]
        # выводим навыки
        bot.send_message(message.chat.id, 'Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)

# функция для сохранения навыка в проекте
def set_skill(message, project_name, skills):
    # берем сообщение
    skill = message.text
    # id пользователя
    user_id = message.from_user.id
    # проферка на закрытие
    if message.text == cancel_button:
        cansel(message)
        return
    
    # если нет скила
    if skill not in skills:
        bot.send_message(message.chat.id, 'Видимо, ты выбрал навык. не из спика, попробуй еще раз!) Выбери навык', reply_markup=gen_markup(skills))
        bot.register_next_step_handler(message, set_skill, project_name=project_name, skills=skills)
        return
    # добовляем скил к проекту
    manager.insert_skill(user_id, project_name, skill )
    bot.send_message(message.chat.id, f'Навык {skill} добавлен проекту {project_name}')

# команда для вывода всех проктов пользователя
@bot.message_handler(commands=['projects'])
def get_projects(message):
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        bot.send_message(message.chat.id, text, reply_markup=gen_inline_markup([x[2] for x in projects]))
    else:
        no_projects(message)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    project_name = call.data
    info_project(call.message, call.from_user.id, project_name)

# команда для удаления проекта
@bot.message_handler(commands=['delete'])
def delete_handler(message):
    # берем id юзера и проекты
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    if projects:
        # выводим список проектов
        text = "\n".join([f"Project name:{x[2]} \nLink:{x[4]}\n" for x in projects])
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, text, reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
    else:
        # нет проектов
        no_projects(message)

# функция для удаления проекта
def delete_project(message, projects):
    project = message.text
    user_id = message.from_user.id

    # проверка на закрытие
    if message.text == cancel_button:
        cansel(message)
        return
    # если нет такого проекта
    if project not in projects:
        bot.send_message(message.chat.id, 'У тебя нет такого проекта, попробуй выбрать еще раз!', reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, delete_project, projects=projects)
        return
    # удаляем проект и пишем об этом
    project_id = manager.get_project_id(project, user_id)
    manager.delete_project(user_id, project_id)
    bot.send_message(message.chat.id, f'✅ Проект {project} удален! ✅')


# команда для обновления проекта
@bot.message_handler(commands=['update_projects'])
def update_project(message):
    # берем информацию
    user_id = message.from_user.id
    projects = manager.get_projects(user_id)
    # выводим список проектов
    if projects:
        projects = [x[2] for x in projects]
        bot.send_message(message.chat.id, "Выбери проект, который хочешь изменить", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
    else:
        no_projects(message)

# обновление 2 ступень
def update_project_step_2(message, projects):
    # сообщение
    project_name = message.text
    # проверка на закрытие
    if message.text == cancel_button:
        cansel(message)
        return
    # если что то пошло не так
    if project_name not in projects:
        bot.send_message(message.chat.id, "Что-то пошло не так!) Выбери проект, который хочешь изменить еще раз:", reply_markup=gen_markup(projects))
        bot.register_next_step_handler(message, update_project_step_2, projects=projects )
        return
    # выбор изменения
    bot.send_message(message.chat.id, "Выбери, что требуется изменить в проекте", reply_markup=gen_markup(attributes_of_projects.keys()))
    bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)

# обновление 3 ступень
def update_project_step_3(message, project_name):
    # берем инфу
    attribute = message.text
    reply_markup = None 
    # если закрыли
    if message.text == cancel_button:
        cansel(message)
        return
    # если нет таколго атрибута
    if attribute not in attributes_of_projects.keys():
        bot.send_message(message.chat.id, "Кажется, ты ошибся, попробуй еще раз!)", reply_markup=gen_markup(attributes_of_projects.keys()))
        bot.register_next_step_handler(message, update_project_step_3, project_name=project_name)
        return
    # если атрибут это статус
    elif attribute == "Статус":
        rows = manager.get_statuses()
        reply_markup=gen_markup([x[0] for x in rows])
    bot.send_message(message.chat.id, attributes_of_projects[attribute][0], reply_markup = reply_markup)
    bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attributes_of_projects[attribute][1])

# обновление 4 ступень
def update_project_step_4(message, project_name, attribute): 
    # берем сообщение
    update_info = message.text
    # проверка на статус
    if attribute== "status_id":
        rows = manager.get_statuses()
        if update_info in [x[0] for x in rows]:
            update_info = manager.get_status_id(update_info)
        # проверка на закрытие
        elif update_info == cancel_button:
            cansel(message)
        # если нет такого статуса
        else:
            bot.send_message(message.chat.id, "Был выбран неверный статус, попробуй еще раз!)", reply_markup=gen_markup([x[0] for x in rows]))
            bot.register_next_step_handler(message, update_project_step_4, project_name=project_name, attribute=attribute)
            return
    # выполняем все команды
    user_id = message.from_user.id
    data = (update_info, project_name, user_id)
    manager.update_projects(attribute, data)
    bot.send_message(message.chat.id, "✅ Готово! Обновления внесены!) ✅")

# проверка на сообщение
@bot.message_handler(func=lambda message: True)
def text_handler(message):
    user_id = message.from_user.id
    projects =[ x[2] for x in manager.get_projects(user_id)]
    project = message.text
    if project in projects:
        info_project(message, user_id, project)
        return
    bot.reply_to(message, "Тебе нужна помощь?")
    info(message)

# запуск
if __name__ == '__main__':
    manager = DB_Manager(DATABASE)
    bot.infinity_polling()