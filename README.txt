Database tables required: game_rooms,players,users,mcq_questions,paragraph_questions,picture_questions,fill_questions
Installation: flask, bcrypt,mysql,mysql connector,python.
Tree structure of project:

├── app.py
├── db_config.py
├── __pycache__
│   ├── app.cpython-312.pyc
│   ├── db_config.cpython-312.pyc
│   └── db_config.cpython-313.pyc
├── static
│   ├── css
│   │   ├── create2.css
│   │   ├── create.css
│   │   ├── fillblanks.css
│   │   ├── home2.css
│   │   ├── home.css
│   │   ├── join.css
│   │   ├── leaderboard.css
│   │   ├── lobby.css
│   │   ├── login.css
│   │   ├── logout.css
│   │   ├── mcq.css
│   │   ├── picture.css
│   │   ├── play_mcq.css
│   │   ├── play_paragraph.css
│   │   ├── play_picture.css
│   │   └── signup.css
│  
└── templates
├── base.html
├── create.html
├── fillblanks.html
├── game_lobby.html
├── home2.html
├── home.html
├── join.html
├── leaderboard.html
├── login.html
├── logout.html
├── mcq.html
├── paragraph.html
├── picture.html
├── play_fillblanks.html
├── play_mcq.html
├── play_paragraph.html
├── play_picture.html
└── signup.html
