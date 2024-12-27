import discord
from discord.ext import commands
from discord.ui import Button, View
import random
from heroes import heroes
import os

# Укажите свой ID
owner_ident = os.getenv('OWNER_IDENT')
OWNER_ID = int(owner_ident)  # Замените на ваш ID

# Список героев League of Legends

# Инициализация бота
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

class BanHeroesView(View):
    def __init__(self, heroes, callback, authorized_user):
        super().__init__()
        self.heroes = heroes
        self.callback = callback
        self.authorized_user = authorized_user
        for index, hero in enumerate(heroes):
            self.add_item(BanButton(hero, index, self.process_ban))

    async def process_ban(self, interaction: discord.Interaction, index: int):
        if interaction.user != self.authorized_user:
            await interaction.response.send_message("Вы не можете нажимать эту кнопку!", ephemeral=True)
            return
        banned_hero = self.heroes.pop(index)
        self.clear_items()
        for idx, hero in enumerate(self.heroes):
            self.add_item(BanButton(hero, idx, self.process_ban))
        await self.callback(interaction, banned_hero, self.heroes)

class BanButton(Button):
    def __init__(self, hero_name, index, process_callback):
        super().__init__(label=f"Ban {hero_name}", style=discord.ButtonStyle.danger)
        self.index = index
        self.process_callback = process_callback

    async def callback(self, interaction: discord.Interaction):
        await self.process_callback(interaction, self.index)

@bot.event
async def on_ready():
    print(f"Бот запущен как {bot.user}!")
    try:
        await bot.tree.sync()  # Синхронизация слэш-команд
        print("Слэш-команды синхронизированы!")
    except Exception as e:
        print(f"Ошибка синхронизации слэш-команд: {e}")

@bot.tree.command(name="setheroes", description="Начать матч с выбором героев")
async def setheroes(interaction: discord.Interaction, member1: discord.Member, member2: discord.Member):
    if interaction.user.id != OWNER_ID:
        await interaction.response.send_message("Вы не можете использовать эту команду!", ephemeral=True)
        return

    # Проверяем, есть ли доступ к каналу
    if interaction.channel is None:
        await interaction.response.send_message("Ошибка: Канал недоступен для выполнения команды.", ephemeral=True)
        return
    
    # Проверяем, есть ли у бота право отправлять сообщения
    if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
        await interaction.response.send_message("Ошибка: Бот не имеет права отправлять сообщения в этом канале.", ephemeral=True)
        return

    selected_heroes = random.sample(heroes, 3)

    # Шаг 1: Сообщение, которое видно всем, с выбранными героями
    await interaction.response.send_message(
        f"Выбранные герои для матча: {', '.join(selected_heroes)}"
    )

    # Шаг 2: Сообщение для первого участника с кнопками
    async def first_callback(interaction: discord.Interaction, banned_hero, remaining_heroes):
        # Проверяем доступ к отправке сообщения
        if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message("Бот не может отправить сообщение в канал.", ephemeral=True)
            return
        
        await interaction.channel.send(
            f"{interaction.user.mention} забанил героя {banned_hero}."
        )
        # Переход ко второму этапу: кнопки для второго участника
        view = BanHeroesView(remaining_heroes, second_callback, member2)
        await interaction.channel.send(
            f"{member2.mention}, выберите героя для бана из оставшихся: {', '.join(remaining_heroes)}",
            view=view
        )

    # Шаг 3: Сообщение для второго участника с кнопками
    async def second_callback(interaction: discord.Interaction, banned_hero, remaining_heroes):
        if not interaction.channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message("Бот не может отправить сообщение в канал.", ephemeral=True)
            return
        
        await interaction.channel.send(
            f"{interaction.user.mention} забанил героя {banned_hero}."
        )
        # Шаг 4: Сообщение с оставшимся героем
        chosen_hero = remaining_heroes[0]
        await interaction.channel.send(
            f"Матч {member1.mention} vs {member2.mention} - выбранный герой: {chosen_hero}"
        )

    # Создание кнопок для первого участника
    view = BanHeroesView(selected_heroes, first_callback, member1)
    await interaction.channel.send(
        f"{member1.mention}, выберите героя для бана из следующих: {', '.join(selected_heroes)}",
        view=view
    )


bot_token = os.getenv('BOT_TOKEN')
bot.run(bot_token)
