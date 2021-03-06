from random import randrange
from db.database import DataBaseConnection
from vk_api import VkApi
from vk_api.keyboard import VkKeyboard
from vk_api.longpoll import VkLongPoll

class MyBotFunctions():

    def __init__(self, token, user_token) -> None:
        self.vk = VkApi(token=token)
        self.user_vk = VkApi(token=user_token) # не все методы работают с GROUP_TOKEN
        self.longpoll = VkLongPoll(self.vk)
        self.db = DataBaseConnection()
        self._count = 1


    def write_msg(self, user_id: int, message: str, keyboard: VkKeyboard=None) -> None: 

        '''Отправляет пользователю с id=user_id сообщение с текстом message, можно прикрепить клавиатуру'''

        params = {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7)}
        if keyboard is not None:
            params['keyboard'] = keyboard.get_keyboard()
        self.vk.method('messages.send', params)


    def find_city(self, query): 
        
        '''Находить id города по запросу query. Возвращает первые 10 результатов'''

        params = {'q': query, 'country_id': 1}
        response = self.user_vk.method('database.getCities', params)
        return response['items'][:5]


    def register_user(self, user_id: int) -> None: 

        """Добавляет id пользователя, пол и id города в таблицу users базы данных"""

        fields_to_get = ['city', 'sex', 'bdate']
        response = self.vk.method('users.get',
                                 {'user_id': user_id,
                                  'fields': ', '.join(fields_to_get)
                                  })[0]
        id = int(response['id'])
        city_id = int(response.get('city', {'id': 0})['id'])
        sex_id = int(response.get('sex', 0))   
        self.db.register_user(id, city_id, sex_id)


    def find_suitable_users(self, city_id, sex_id, age, offset): 

        """Находит id пользователей подоходящих по указанным критериям
           city_id - id города;
           sex_id - id пола;
           age_from - возраст от;
           age_to - возраст до;"""

        params = {'city': city_id, 'sex': sex_id,
                  'age_from': age, 'age_to': age,
                  'has_photo': 1, 'offset': offset,
                  'fields': 'relation, last_seen', 'is_closed': 'false',
                  'count': self._count}
                  
        response = self.user_vk.method('users.search', params)
        
        user = response['items'][0] 
        return user


    def get_top_3_photo(self, user_id):

        '''Возвращает топ-3 фотографии максимального размера отсортированные по сумме лайков и комментариев'''

        params = {'owner_id': user_id, 'album_id': 'profile', 'extended': 1}
        response = self.user_vk.method('photos.get', params)
        photos = response['items']
        sorted_photo = sorted(photos, reverse=True, key=lambda photo: int(photo['likes']['count']))[:3]
        photo_ids = [photo['id'] for photo in sorted_photo]
        return photo_ids


    def send_media(self, user_id, media_owner_id, media_ids: list, message, keyboard: VkKeyboard=None, media_type='photo'):
       
        '''Отправлет user_id фотографии по id владельца и id фотографии, с текстом message и клавиатурой  keyboard'''

        media_urls = [f'{media_type}{media_owner_id}_{media_id}' for media_id in media_ids]
        params = {'user_id': user_id, 'message': message,
                  'attachment': ','.join(media_urls), 'random_id': randrange(10 ** 7)}
        if keyboard is not None:
            params['keyboard'] = keyboard.get_keyboard()
        self.vk.method('messages.send', params)

    def get_user(self, user_id):
        params = {'user_ids': user_id,
                  'fields': 'last_seen, bdate, city, sex'
                  }
                  
        response = self.user_vk.method('users.get', params)
        user = response[0]
        return user