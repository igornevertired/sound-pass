class UserDataHandler:
    def __init__(self):
        self.user_data = {}

    def add_user(self, chat_id):
        if chat_id not in self.user_data:
            self.user_data[chat_id] = {}

    def update_user_step(self, chat_id, step):
        if chat_id not in self.user_data:
            self.add_user(chat_id)
        self.user_data[chat_id]["step"] = step

    def update_user_data(self, chat_id, key, value):
        if chat_id not in self.user_data:
            self.add_user(chat_id)
        self.user_data[chat_id][key] = value

    def get_user_data(self, chat_id):
        return self.user_data.get(chat_id, {})

    def delete_user(self, chat_id):
        if chat_id in self.user_data:
            del self.user_data[chat_id]