# 🌍 Online school engine for englishful.ru 🌍
## What is it? 🧐
This is an online platform that simplifies teaching & learning english by doing the following:
1. You can create personalized student accounts.
2. You can assign students to groups.
3. You can create staff (teacher) accounts and assign students to these teachers. There are also master accounts (superusers) that have extended capabilities than the ones of teachers.
4. Students can solve tests, add words to their dictionary, train words via flashcards, listen to word pronunciations, browse through their study plan & more....
## 🌟 Main Features 🌟
* 📱 Responsive mobile-friendly design. The website looks just like a mobile app from a smartphone.
* 🙋 Personalized profile with GPA, test results, CEFR lvl & progress scale, and more.
* 📑 Tests with instant check & explanation. Test results are saved and displayed in student's profie. Students have the ability to retake tests and see their mistakes in their profile.
* 📚 Theory section with links to google docs with theory.
* 📖 Dictionary with features like:
> * Ability to add words.
> * Words training via flashcards. Each word and word topic have their own progress scale. Also there is a general progress scale of all words in a student's dictionary.
> * Ability to listen to words' pronunciation & usage in context. Students can also adjust the speaker speed.
> * & more...

## 🔧 Technology Stack 🔧
* Django (4.1.5), Python (3.11), MySQL, JavaScript, SCSS, and HTML.

## Dependencies
* You can install all dependencies (bleach==6.0.0, Django==4.1.5) and start getting your hand on the project by doing the following:
1. Execute **"pip install -r requirements.txt"** in root folder.
2. Execute **"python manage.py runserver"** in root folder.
* **Done** ✔️
> * For simplicity I decided to use **sqlite** in the public version so that it would be easier to get the things going.
> * I created three example users for you:
>> * login: admin / password: admin - the admin account.
>> * login: student_number_one / password: student#1 - example student #1.
>> * login: student_number_two / password: student#2 - example student #2.

## &#128194; Entry Points &#128194;
1. requirements.txt - project requirements.
2. db.sqlite3 - database.
3. website\static - all static files like css, images, js, etc.
4. website\static\website\js\main.js - main JavaScript file.
5. website\templates - html pages.
6. website\views.py - main backend logic.
7. website\urls.py - routing.
8. website\models.py - database configuration.
9. website\admin.py - admin panel tuning.
10. scuh\settings.py - project settings.

## ❗Important❗
* If you actually get your hands on this projects and think that it is usefull for learning / teaching english you can contact me and consult on the topic of adding tests, theory topics & just managing the website through the admin panel.
* I started this project when I was only beginning my coding journey and didn't know much about code maintanability, best practices & more. Therefore, lots of code in this project does need refactoring. I am not doing this because currently I am actively leveling up my JS & React skills and want to implement a similar project using next.js. Once I reimplement the project in next.js from scratch I will deploy it and replace the current django implementation with it.
1. Yes, I know that the "website\static\website\css\main.scss" file **must** be refactored.
2. Yes, I know that the same thing **must** be done to the "website\views.py" file in order to make code more modular and thus more maintainable for futre scaling.
3. & more...I guess you get the point.
