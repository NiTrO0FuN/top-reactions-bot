
# Top Reactions Bot

Discord bot that ranks top reacted messages on a podium 🏆 ! 

Official invite link: [Invite](https://discord.com/api/oauth2/authorize?client_id=1183036134792638494&permissions=277025614912&scope=bot) 


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

`DISCORD_TOKEN`


## Run the bot

Clone the project

```bash
  git clone https://github.com/NiTrO0FuN/top-reactions-bot.git
```

Go to the project directory

```bash
  cd top-reactions-bot
```

Virtual environment
  - Create the virtual environment (first time only)
    ```bash
      python -m venv <name_of_virtualenv>
    ```
  - Activate it
    - Windows
    ```cmd
      <name_of_virtualenv>\Scripts\activate.bat
    ```
    - Linux + macOS
    ```bash
      source <name_of_virtualenv>/bin/activate
    ```
    
Install dependencies

```bash
  pip install -r requirements.txt
```

Create the database (first time only)

```bash
  python db_helpers/create_db.py
```

Start the bot

```bash
  python bot.py
```

